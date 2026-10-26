+++
title = "Fe 26.5.0"
date = "2026-10-26"
+++

<!-- Editorial note: release-day copy, based on argotorg/fe master at
0e858372ca2ec7aed766b99f64459cefc708fe40 (2026-10-26), compared with v26.4.1.
All Fe examples were checked with a release build of that commit. Confirm the
release tag and platform artifacts, set the date, and remove draft status
before publishing. -->

The Fe team is happy to announce the release of Fe 26.5.0!

This is the biggest Fe release so far. Fe now has mutable value semantics:
references are no longer values, and a new access checker replaces the borrow
checker. The release also adds closures, tuple structs, `unsafe` blocks, and
const `where` predicates. Typed ETH amounts and timestamps are new, storage
layouts are now Solidity-compatible, and the standard library has grown
considerably. The native backend now ships in the release binaries. Contracts
are smaller and cheaper, and the compiler is faster.

Many of these changes are breaking; the [upgrade notes](#upgrading-from-26-4)
at the end summarize what existing code needs. Highlights are below; the full
changelog is here: [v26.5.0](https://github.com/argotorg/fe/releases/tag/v26.5.0)

## Mutable value semantics

Every value in Fe now has exactly one owner, and a reference is never a value.
`ref` and `mut` are no longer types, so a struct cannot hold a borrow. Instead,
they describe how a function or binding *accesses* a place owned by someone
else. An access exists only as a parameter, a binding, or the result of a
call, and it ends at its last use.

A parameter is a read-only view (`x: T`), a mutable access (`x: mut T`), or
owned (`x: own T`). A binding can take an access too: `let h = mut p.x` gives
mutable access to `p.x` until the last use of `h`. Two accesses conflict only
when they overlap and at least one of them writes, so a function can hold
mutable access to two different fields of a struct at the same time:

```rust
struct Account {
    balance: u256,
    nonce: u256,
}

fn credit(_ balance: mut u256, amount: u256) {
    balance += amount
}

#[test]
fn accesses() {
    var acct = Account { balance: 10, nonce: 0 }

    // Two mutable accesses to different fields of one struct.
    let b = mut acct.balance
    let n = mut acct.nonce
    b += 5
    n += 1

    credit(mut acct.balance, amount: 5)
    assert!(acct.balance == 20)
    assert!(acct.nonce == 1)
}
```

Mutable variables are now declared with `var x = e`, which replaces
`let mut x = e`. In patterns, `mut`, `ref`, and `var` mark the individual names
being bound, as in `Some(mut v)` or `for mut x in xs`.

### Projections

A function that returns `ref T` or `mut T` gives its caller access to a place
rather than a copy of a value. We call such a function a *projection*. The
caller can assign through the result directly or bind it like any other
access:

```rust
struct Counter {
    hits: u256,
    misses: u256,
}

impl Counter {
    fn slot(mut self, hit: bool) -> mut u256 {
        if hit { mut self.hits } else { mut self.misses }
    }
}

#[test]
fn projections() {
    var c = Counter { hits: 0, misses: 0 }
    c.slot(hit: true) += 2
    let m = mut c.slot(hit: false)
    m += 1
    assert!(c.hits == 2)
    assert!(c.misses == 1)
}
```

A projection can also `yield` its access and run code after the caller's last
use of it, for example to write a modified value back to storage. Results can
be shapes such as `Option<mut T>`, and a `mut?` function is written once and
checked for both read and write use. Indexing, `MemBuffer::span`, and many
other library methods now use this to replace separate `foo` and `foo_mut`
methods.

### The access checker

A new access checker replaces the borrow checker. It works on a simpler model,
since there are no reference values to track: each access lasts until its last
use, and overlapping accesses conflict unless both only read. The
[accesses guide](https://github.com/argotorg/fe/blob/master/docs/language/accesses.md)
describes the rules in detail.

## Closures and iteration

Fe now has closures, such as `|x| x + 1` or
`|acc: own u256, x: u256| -> u256 { acc + x }`. A closure can be passed to any
function that takes a callable, including `fold`, `any`, `count`, and `find` on
collections, and to the `filter` and `map` loop adapters. A named function can
be passed wherever a closure can.

Loops are driven by method chains on the collection: `xs.enumerate()`,
`xs.reversed()`, `xs.enumerate().take(3)`, or `xs.filter(..)`. A loop pattern
can take the step apart, as in `for (i, x) in xs.enumerate()`.

```rust
#[test]
fn closures() {
    let xs: [u256; 5] = [1, 2, 3, 4, 5]

    let sum_of_squares = xs.fold(0, |acc: own u256, x: u256| -> u256 { acc + x * x })
    assert!(sum_of_squares == 55)

    var evens = 0
    for x in xs.filter(|x| x % 2 == 0) {
        evens += x
    }
    assert!(evens == 6)

    for (i, x) in xs.enumerate() {
        assert!(x == i as u256 + 1)
    }
}
```

Generic functions take a callable with a bound such as `F: Fn(u256) -> bool`
and call it as `f(x)`. Closures work in contract code too, where their bodies
can use the contract's storage and other effects; a generic function that
calls a closure declares `uses F::E` so that its callers provide those effects.

A closure captures the values it uses by copy or move and cannot modify them,
so state is passed through parameters and results, as `fold` does. Function
and closure parameters can also be patterns, as in
`pairs.fold(0, |acc, (a, b)| acc + a * b)`.

## Tuple structs

Tuple structs make newtypes much lighter to write. A tuple struct is
constructed by calling its name, accessed by position, and destructured with a
tuple pattern:

```rust
struct Month(pub u8)

fn days_in(_ m: Month) -> u8 {
    match m {
        Month(2) => 28,
        Month(4) | Month(6) | Month(9) | Month(11) => 30,
        _ => 31,
    }
}

#[test]
fn tuple_structs() {
    var m = Month(10)
    assert!(m.0 == 10)
    m.0 = 2
    assert!(days_in(m) == 28)
}
```

Tuple structs can be generic, have `where` clauses, and be used as contract
storage fields. `#[event]`, `#[error]`, and `#[abi]` remain limited to structs
with named fields.

## `unsafe` blocks

Dereferencing a raw pointer or calling an `unsafe fn` now requires an
`unsafe { .. }` block or an `unsafe fn`. A struct or enum field can be declared
`unsafe` when safe code relies on its value, such as a buffer's length: reading
it is safe, but setting or mutating it requires `unsafe`.

A dependency's `unsafe` code, including its `unsafe impl`s, can only be used if
`fe.toml` trusts the dependency with `allow_unsafe = true`.

## Const `where` predicates

Items can now state boolean conditions on their const generic parameters. The
condition is checked wherever the item is used, so invalid instantiations are
rejected at compile time:

```rust
struct Ring<const N: usize> where N > 0 {
    slots: [u256; N],
}

const fn is_power_of_two(_ n: usize) -> bool {
    n != 0 && (n & (n - 1)) == 0
}

fn mask<const N: usize>() -> usize where is_power_of_two(N) {
    N - 1
}

#[test]
fn const_predicates() {
    let r = Ring<4> { slots: [0; 4] }
    assert!(r.slots[3] == 0)
    assert!(mask<8>() == 7)
    // `Ring<0>` or `mask<6>()` is rejected at compile time.
}
```

A generic caller satisfies a condition only by stating the same condition.
Array repeat lengths and array types computed from generic parameters, such as
`[0; N + 1]` or `[u8; T::LEN]`, are now accepted as well.

## Typed ETH amounts and time

`std::evm::units` adds `Wei` (an amount of native ETH), `Timestamp` (unix
seconds), and `Duration` (seconds). The three types are in the std prelude,
and they don't mix: `Timestamp + Duration` is a `Timestamp`,
`Timestamp - Timestamp` is a `Duration`, and `Timestamp + Timestamp` or
`Wei + Duration` do not compile.

```rust
use std::evm::{days, ether, gwei, weeks}

const LOCK: Duration = weeks(2) + days(3)

fn unlock_time(_ deposited_at: Timestamp) -> Timestamp {
    deposited_at + LOCK
}

fn fee(_ amount: Wei) -> Wei {
    amount.mul_div(numerator: 3, denominator: 1000)
}

#[test]
fn units() {
    let start = Timestamp::from_seconds(1_700_000_000)
    assert!(unlock_time(start) - start == days(17))
    assert!(fee(ether(1)) == gwei(3_000_000))
    // `start + start` or `ether(1) + days(1)` would not compile.
}
```

The constructors `ether`, `gwei`, `wei`, `days`, `hours`, and friends are
`const fn`s, so they work in constant initializers. All three types are a
single `uint256` in the ABI, so they can be `msg` fields, return values, event
fields, contract fields, and `StorageMap` keys or values.

The standard library uses them throughout: `Ctx::value` and `Ctx::balance`
return `Wei`, `Ctx::timestamp` returns `Timestamp`, and every `value`
parameter of the call and create APIs takes `Wei`. Write `value: Wei::zero()`
where you previously wrote `value: 0`.

## Solidity-compatible storage

Storage layouts have been reworked to match Solidity's more closely. Narrow
struct fields now share slots the way Solidity packs struct members, and
`StorageMap` values use their type's native layout. Narrow signed values are
stored as their own two's-complement bytes, and storage and transient fields
are numbered separately.

Storage collections are no longer `Copy` handles and no longer take `SALT`
parameters. A collection takes its slot from the contract field that holds it,
so collections are passed as `mut` or view parameters instead of by value.
Transient fields are declared as `TSlot<T>` and accessed as `field.value`.

New collections and helpers make it easier to work with existing Solidity
layouts:

- `std::evm::SolArray` for Solidity dynamic storage arrays (`T[]`), with small
  elements packed like Solidity, and `std::evm::SolEnumerableSet` for
  OpenZeppelin `EnumerableSet` storage.
- `SolSlot::load` returns a `SolWord` for reading or updating several packed
  fields of a slot with a single `sload`/`sstore`.
- `std::evm::layout` provides Solidity's slot derivations: `mapping_slot`,
  `array_data_slot`, and `element_location`.
- `std::evm::heap::StorageHeap<T>`, a binary min-heap in storage after
  Solady's `MinHeapLib`.

Note that the layout changes mean that contracts compiled with 26.5 do not
share a storage layout with the same source compiled by 26.4.

## Solidity ABI interop

The new `#[abi]` struct attribute encodes a struct like the Solidity tuple of
its fields. Solidity structs such as Uniswap's `PoolKey` can now be used in
`msg` fields and return types, in arrays, and inside other `#[abi]` structs
without hand-written codecs:

```rust
use std::abi::sol::{Int24, Uint24}

#[abi]
struct PoolKey {
    currency0: Address,
    currency1: Address,
    fee: Uint24,
    tick_spacing: Int24,
    hooks: Address,
}

msg PoolMsg {
    #[selector = sol("register((address,address,uint24,int24,address))")]
    Register { key: PoolKey } -> u256,
}

pub contract Pools {
    mut count: u256,

    recv PoolMsg {
        Register { key } -> u256 uses (mut count) {
            count += 1
            count
        }
    }
}
```

`#[abi]` structs whose fields all have Solidity types can also be `#[event]`
and `#[error]` fields. Other ABI improvements:

- `DynArray` can be indexed and looped over for every ABI element type,
  including multi-word structs, tuples, and dynamic elements such as `Bytes`.
- `std::abi::ArrayView` is a lazy view of a Solidity `T[]` in calldata. It
  validates offsets and lengths like a Solidity `T[] calldata` parameter and
  decodes elements one at a time, so raw-selector `recv` arms can read large
  arrays without decoding them into memory.
- Enums with a `SolCompat` implementation can be `msg` fields.
- Generated JSON ABIs no longer list Solidity's built-in `Error` and `Panic`,
  so ethers can load contracts with panic paths.

## Standard library

Beyond storage and ABI, the standard library gains many modules that port
well-known Solidity libraries. Most are written to match the behavior of their
OpenZeppelin or Solady counterparts exactly.

For EVM applications:

- `std::evm::signature`: ECDSA recovery (including EIP-2098 compact
  signatures) and ERC-1271 checks with OpenZeppelin `SignatureChecker`
  semantics.
- `std::evm::eip712`: domain separators and digests, with a `Domain` type that
  caches the separator like OpenZeppelin's `EIP712`.
- `std::evm::multicall`: the counterpart of OpenZeppelin's `Multicall`.
- `std::evm::erc4337`: building blocks for ERC-4337 accounts and paymasters on
  EntryPoint v0.7 and v0.8.
- `std::evm::rlp`: RLP encoding and decoding.
- `std::evm::random`: pseudorandom numbers as an effect, after Solady's
  `LibPRNG`. Tests can substitute a `ReplayRng` to drive code to specific
  outcomes.
- Revert helpers such as `bubble_revert_or`, `decode_error_string`, and
  `decode_panic`, and `ReturnData` for reading returndata in place.
- `init_code_hash<C>(args)` and `predict_create2<C>(deployer, args, salt)` for
  predicting the address of a contract deployed with `create2<C>`.

For general-purpose code:

- `core::fixed` provides decimal fixed-point numbers with the scale in the
  type: `UFixed<D>`, `Fixed<D>`, and the aliases `Wad`, `Ray`, and `SWad`.
  Mixing scales, as in `Wad * Ray`, is a type error. The 18-decimal types port
  Solady's `expWad`, `lnWad`, and `powWad` bit for bit.
- `core::sort` provides sorting and searching after Solady's `LibSort`,
  generic over both the container and the element.
- `MemVec<T>` is now a growable in-memory array for any element type.
- `core::mem::replace` and `core::mem::take` move a value out of a place
  while leaving another one behind.
- `core::text` can parse numbers (`parse_uint`, `parse_int`,
  `parse_hex_uint`) and decode base64 and base58; `std::evm::parse_address`
  parses addresses.
- `core::num::gcd` computes the greatest common divisor.

Fixed-point arithmetic and sorting, for example, look like this:

```rust
use core::fixed::Wad
use core::sort

const FEE: Wad = Wad::from_ratio(3, 1000)

#[test]
fn fixed_point() {
    let fee = Wad::from_int(250) * FEE
    assert!(fee == Wad::from_ratio(3, 4))
}

#[test]
fn sorting() {
    var xs: [u256; 6] = [42, 7, 19, 7, 3, 100]
    sort::sort(mut xs)
    assert!(xs == [3, 7, 7, 19, 42, 100])
    assert!(sort::binary_search(xs, 19).unwrap() == 3)
}
```

String literals longer than 31 bytes are now `DynString` values when their
context doesn't fix a type, so `let reason = "a long revert reason ..."` just
works.

## Native executables in the release binaries

As announced with 26.4, the release binaries now include the native backend.
On x86-64 Linux and AArch64 macOS, the prebuilt `fe` can build host-native
executables directly:

```rust
pub fn main() -> i32 {
    0
}
```

```sh
fe build --backend native --out-dir out hello.fe
./out/hello
```

Native executables are now the backend's default output, so `--emit executable`
is no longer needed. On the other release targets, the native backend is
available for `--emit ir`. Native test suites also compile much faster, since
they now share one runtime package across all modules.

We are already using native Fe ourselves: the release notes for this release
were assembled by [eisenbote](https://github.com/fe-lang/eisenbote), a
replacement for the Python-based [towncrier](https://towncrier.readthedocs.io/)
written in Fe and compiled with the native backend. It reads its settings with
[lutz](https://github.com/fe-lang/lutz), a TOML parser written in Fe, and
produces the same bytes as towncrier, which its test suite checks by replaying
all 38 Fe releases since 2021. Our release pipeline builds eisenbote with the
compiler that is about to be released, so every release now also compiles and
runs a real native Fe program.

This release also adds experimental compilation of Fe programs as SP1 RV64IM
zkVM guests. It is not part of the release binaries; build the compiler from
source with the `sp1` feature to try it.

## Gas, bytecode size, and compilation

The Sonatina backend received several improvements that make contracts smaller
and cheaper:

- Values are reordered on the EVM stack with the fewest swaps, and the backend
  reloads only the values it needs instead of spilling the whole stack. The
  eight contracts of a Fe port of Seaport shrink by 5.4% at `-O1`.
- Messages and errors are encoded in place after their selector instead of
  being encoded and then copied. The same Seaport contracts shrink by another
  1.7% at `-Os`.
- Loops end each iteration in one conditional branch. Verifying a 64-level
  Merkle proof drops from 11,428 to 10,718 gas.
- In the Ethereum deposit contract, `deposit` uses about 130 gas less, and the
  runtime shrinks from 2,360 to 2,281 bytes.

These numbers come from the individual benchmarks; the effect on other
contracts depends on how they use the affected operations.

The compiler itself is faster too. The parser is about twice as fast, function
bodies in `core` and `std` are only lowered when needed, and `fe test` compiles
a file's tests in parallel. Running `fe test` on each of the compiler's 385
test fixtures takes a quarter less time and half the CPU. Checking deeply
nested generic types no longer takes exponential time.

## Other fixes

A few more changes worth calling out:

- An operator after an `if`/`else` expression now applies to the whole
  conditional. In 26.4, `if c { 1 } else { 2 } + 3` was silently parsed as
  `if c { 1 } else { 2 + 3 }`.
- Code after an `if`/`else` chain is no longer skipped when the last branch
  diverges but an earlier one falls through.
- Several EVM memory miscompiles in optimized builds are fixed, including a
  buffer allocated before a loop reusing memory that the loop still reads.
- An `Address` can no longer hold bits above the low 160, so two addresses for
  the same account are always equal, the same map key, and the same event
  topic. Build one with `Address::new(word)` and read it with `address.word()`.
- `Option<T>` is now `Copy` when `T` is, and `Result<E, T>` when both are.
- Import resolution no longer depends on the order of `use` items, and
  ambiguous names list every candidate.
- `fe fmt` no longer drops `pub(ingot)` or `pub(super)`, attributes on `for`
  loops, or comments in certain positions.
- Find references, rename, and highlighting in the language server are much
  more accurate, and no longer edit the same reference twice.

## Upgrading from 26.4

Most existing code needs changes to build with 26.5. The most common ones:

- Replace `let mut x = ...` with `var x = ...`, and remove `ref` and `mut` from
  types. Fields can no longer hold references; pass accesses as parameters
  instead.
- Pass ETH amounts as `Wei` and timestamps as `Timestamp`, for example
  `value: Wei::zero()` instead of `value: 0`.
- Drop `SALT` parameters and `= _` layout defaults from storage collections,
  and pass collections as `mut` or view parameters. Declare transient fields
  as `TSlot<T>`.
- Build addresses with `Address::new(word)` instead of `Address { inner: .. }`.
- Collection lengths and indices are now `usize` instead of `u256`.
- Paired methods such as `span_mut` and `IndexMut` are replaced by single
  `mut?` methods and `mut Index` bounds.
- Wrap raw-pointer dereferences and calls to `unsafe fn` in `unsafe { .. }`.

The [release notes](https://github.com/argotorg/fe/releases/tag/v26.5.0) list
every removal, and the [Fe guide](https://fe-lang.org) has been updated for
26.5.

## Try it!

[Fe 26.5.0](https://github.com/argotorg/fe/releases/tag/v26.5.0) is available
now for Linux, macOS, and Windows. Let us know what you think!

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation
