+++
title = "Fe 26.4 — updated for 26.4.1"
date = "2026-09-30"
+++

> **Update (2026-09-30): Fe 26.4.1 supersedes 26.4.0.**
> Shortly after releasing 26.4.0, we found that the borrow checker incorrectly
> rejected a common contract pattern: calling a mutable method on a contract
> field whose struct contains a `StorageMap` or `StorageBytes` alongside other
> fields. Fe 26.4.1 fixes this regression and includes additional borrow-checking
> fixes. Please use 26.4.1 when trying the features described below.

The Fe team is happy to announce Fe 26.4, now available as Fe 26.4.1!

This release improves borrow checking, adds an experimental native backend,
and expands the standard library with helpers for Solidity storage layouts, external calls,
text formatting, and full-precision arithmetic. It also improves ABI
compatibility, fixes deterministic deployment, and reduces gas, bytecode size,
and compilation time. Highlights are below; the release notes cover the
[26.4.0 features](https://github.com/argotorg/fe/releases/tag/v26.4.0) and the
[26.4.1 fixes](https://github.com/argotorg/fe/releases/tag/v26.4.1).

## Fixes in 26.4.1

The main reason for this patch is a borrow-checking regression that blocked
valid contract logic. Calling a `mut self` method that uses a `StorageMap` or
`StorageBytes` field could produce a false borrow conflict when the receiver
was a contract field whose struct also contained other fields. This affected
calls from `recv` handlers, for example. These calls are now accepted again.

The patch also corrects ownership and borrow checking for compile-time constant
values. Invalid repeated moves of non-`Copy` values and reads that conflict with
a live mutable borrow are now rejected, as they already were for runtime
values. Conversely, passing an unannotated string literal to a generic `own`
parameter more than once no longer produces a false move conflict.

All the features introduced in 26.4.0 and described below are included in
26.4.1. If you installed 26.4.0, please upgrade to the patched release.

## Borrow checking improvements

Fe’s borrow checker now tracks ownership and borrows more precisely through
tuples, structs, arrays, pointer aliases, and helper calls. Borrow information also follows references returned
inside aggregates: returning a reference inside a tuple and then destructuring
it no longer hides that reference from the borrow checker. Overlapping live
borrows are rejected even when they reach the same value through different paths.

The checker also rejects uses of moved non-`Copy` values through pointers,
including pointers returned by calls and accesses to their fields or array
elements. Ownership and borrow requirements on generic calls are checked when
the concrete trait implementation is selected.

### State borrows across external calls

External calls can call back into a contract and access its state. Fe now
accounts for that possibility when checking live borrows of persistent and
transient state.

`CALL`, `DELEGATECALL`, `CREATE`, and `CREATE2` conflict with live state borrows.
`STATICCALL` allows shared state borrows, but conflicts with mutable ones. Code
that holds a conflicting borrow across one of these operations must end the
borrow before making the call.

### Copies and pointer access

Several related fixes make ownership behave consistently:

- Copying an array returned by a function now creates an independent value.
  Modifying the copy no longer changes the original, including for nested arrays.
- Comparisons such as `a == b` borrow a non-`Copy` right-hand operand instead of
  moving it. Shared method calls on non-`Copy` fields also no longer falsely
  consume the field.
- `FixedBytes<N>` now implements `Copy`, so values such as `Bytes32` can be reused
  without a move conflict.
- Fields and array elements reached through temporary pointers can be assigned,
  compound-assigned, and borrowed. Calls such as `(*f()).set(1)` now update the
  pointee instead of silently updating a copy.

## Experimental native executables

Fe can now compile programs to host-native executables on x86-64 Linux and
AArch64 macOS. The native backend uses Cranelift and supports standalone files
as well as whole workspaces with dependencies.

Build the Fe compiler with the `cranelift` feature enabled to try it. A minimal
program uses `pub fn main() -> i32`, with the return value becoming the process
exit code:

```rust
pub fn main() -> i32 {
    0
}
```

Save this as `hello.fe`, then build and run it:

```sh
fe build --backend native --emit executable --out-dir out hello.fe
./out/hello
```

`fe test --backend native` also runs Fe tests as native executables. Reverts,
including failed `assert!` calls with messages, trap on native targets.

The standard library provides the beginnings of a host programming environment:

- `std::io` provides character input and output.
- Programs can receive process arguments through
  `pub fn main(argc: i32, argv: **u8) -> i32` and read them with the
  bounds-checked `std::native::Args` API.
- `std::native::cpu_clock_ticks` exposes process CPU time.
- `std::native::ByteBuffer` provides an explicitly owned heap byte buffer, with
  fallible growth that preserves existing data, zero initialization,
  overlap-safe copying, and an explicit `release` operation.

This backend is experimental. Native references preserve their addresses and
aliasing through aggregate fields, pointer slots, and helper returns. The
compiler rejects loads of references from uninitialized or byte-overwritten
slots; copying raw bytes into a slot does not establish a valid reference.

## More capable const functions

Const functions can now borrow their own locals and parameters with `ref` and
`mut`. Helpers that update a value in place, including helpers taking a `mut`
argument, can therefore run during constant evaluation. Returning a borrow of a
local from the function that owns it is rejected during evaluation.

Const functions can also receive immutable trait providers through `uses` and
supply them with `with`. This includes forwarding providers through generic
const functions, calling const trait methods, and borrowing a provider for a
`ref self` method call. Mutable effects, storage effects keyed by type, and
extern functions with effects remain unsupported in const evaluation.

Generic constants now handle array repeats with symbolic lengths and indices
in branches, enum matches, casts, and type-level expressions. Bounds checks and
assertion diagnostics are preserved when those constants are specialized.

## Solidity storage layouts

The new `std::evm::SolSlot` provides access to Solidity storage layouts at
runtime-selected slots. Its `read` and `write` operations access a packed state
variable at a byte offset without changing its neighbours. Supported values
include booleans, addresses, all integer widths, and fixed bytes, including
custom-width types such as `sol::Int24`.

`read_bytes`, `read_string`, `write_bytes`, and `write_string` use Solidity's
storage representation for dynamic bytes and strings. `std::evm::SolMapping`
derives Solidity-compatible mapping slots from a runtime root, including nested
mappings. These APIs let code work with an existing Solidity layout directly.

For example, a pool layout can pack an address, fee, and tick spacing into
one slot. Each write specifies the field's byte offset:

```rust
use std::abi::sol::{Int24, Uint24}
use std::evm::{Evm, RawStorage, SolSlot}

#[test]
fn packed_pool_parameters() uses (evm: mut Evm) {
    with (RawStorage = evm) {
        // Solidity: address currency; uint24 fee; int24 tickSpacing;
        let slot = SolSlot::at(7)
        slot.write(offset: 0, value: Address { inner: 0xabc })
        slot.write(offset: 20, value: Uint24 { val: 3000 })
        slot.write(offset: 23, value: Int24 { val: 60 })

        // Updating the fee leaves the neighbouring fields intact.
        slot.write(offset: 20, value: Uint24 { val: 500 })
        let currency: Address = slot.read(offset: 0)
        let fee: Uint24 = slot.read(offset: 20)
        let spacing: Int24 = slot.read(offset: 23)
        assert!(currency.inner == 0xabc)
        assert!(fee.val == 500)
        assert!(spacing.val == 60)
    }
}
```

### Custom storage keys

`StorageMap` now reserves its complete hashing buffer before calling a custom
key encoder. Previously, an allocation made during encoding could overwrite
part of the key being hashed.

This changes the `StorageKey` interface: custom implementations must provide
`encoded_len(self) -> u256`, and `write_key` must return `()` instead of the
encoded length. Custom-width Solidity integers now implement `StorageKey` too.

## External calls and token helpers

`Call::try_call_into` and `Call::try_static_into` copy returndata into a
caller-provided buffer, up to that buffer's capacity. This lets callers bound
the amount of data copied even when a callee returns a very large payload.

`Call::call_with_min_gas` adds an EIP-150 gas-budget admission check, accounting
for a caller reserve and prepaid input memory, with no automatic returndata
copy. `Call::send_value` handles plain value transfers, and
`Call::try_call_raw` forwards raw calldata.

Static calls now only require a read-only `Call` effect, including bounded raw
static calls. This preserves `view` mutability in the generated ABI.

### Handling token failures explicitly

Fe 26.3 added ERC-20 helpers that revert on failure. This release adds
non-reverting helpers that return a classified `TokenCall` outcome: `Ok`,
`Reverted`, `BadReturn`, or `NoCode`. Callers can inspect the result and raise
their own errors.

For example, a transfer helper can turn each failure category into a distinct
application error. Here we use revert messages to keep the example small:

```rust
use std::evm::{Call, Ctx, TokenCall, erc20}

fn transfer_or_revert(token: Address, receiver: Address, amount: u256)
uses (call: mut Call, ctx: Ctx) {
    match erc20::try_transfer(token, receiver, amount) {
        TokenCall::Ok => {},
        TokenCall::Reverted => assert!(false, "Token transfer reverted"),
        TokenCall::BadReturn => assert!(false, "Token returned failure"),
        TokenCall::NoCode => assert!(false, "Token address has no code"),
    }
}
```

The new helpers cover:

- ERC-20: `try_transfer`, `try_transfer_from`, and `try_approve`, with a bounded
  32-byte returndata copy.
- ERC-721: `try_transfer_from`.
- ERC-1155: `try_safe_transfer_from` and `try_safe_batch_transfer_from`.

`erc721::check_on_received` also classifies the result of an `onERC721Received`
hook. The new `std::evm::erc165` module provides interface checks matching
OpenZeppelin's `ERC165Checker` semantics.

## Deterministic deployment and minimal proxies

The initcode embedded by `create<B>` and `create2<B>` is now exactly the `B.bin`
artifact produced by `fe build`. Previously, compiling `B` together with the
embedding contract could change helper sharing and inlining, producing different
bytes. A CREATE2 address calculated off-chain from `B.bin` could consequently
differ from the address actually deployed.

Each contract is now compiled independently and embedded as its final bytes.
This also makes a contract's bytecode independent of other contracts declared
in the same file.

`std::evm::create2_address` computes an address from a deployer, salt, and initcode
hash. The new `std::evm::clones` module provides ERC-1167 minimal-proxy initcode,
CREATE and CREATE2 deployment, and deterministic address prediction.

## Full-precision arithmetic and Merkle proofs

`core::num` now provides `mul_div` and `mul_div_ceil`. Both calculate `a * b / d`
using a 512-bit intermediate product, so multiplication can exceed `u256` as
long as the final quotient fits. `mul_div` rounds down; `mul_div_ceil` rounds up.

```rust
use core::num::{mul_div, mul_div_ceil}

#[test]
fn full_precision_example() {
    let scale: u256 = 1 << 200
    assert!(mul_div(scale, scale, scale) == scale)
    assert!(mul_div(10, 10, 6) == 16)
    assert!(mul_div_ceil(10, 10, 6) == 17)
}
```

Division by zero or an overflowing quotient fails like checked arithmetic.
`checked_mul_div` and `checked_mul_div_ceil` return `None` instead. `full_mul`
exposes the full product, while `addmod` and `mulmod` are now also available
through `core::num`.

`leading_zeros` and `trailing_zeros` count zero bits in a `u256`, returning 256
for zero. Both work during constant evaluation. On EVM targets,
`leading_zeros` uses the `CLZ` instruction; the native implementation uses a
branch-free bit search.

For Merkle proofs, `std::evm::merkle` supports both OpenZeppelin-compatible
sorted-pair trees and positional proofs, such as those used in Seaport bulk
order signatures. Proofs are read in place from a `MemSlice<u256>` or a decoded
`DynArray<Bytes32>` / `DynArray<u256>`.

For an allowlist or airdrop, the verification step takes a proof, a trusted
root, and the leaf hash. This small test builds a two-leaf tree and checks both
a valid leaf and one that is not in the tree:

```rust
use std::abi::MemVec
use std::evm::{keccak_words, merkle}

#[test]
fn verify_two_leaf_tree() {
    let leaf = keccak_words([1])
    let sibling = keccak_words([2])
    let root = merkle::hash_pair_sorted(leaf, sibling)

    let mut proof: MemVec<u256> = MemVec::zeroed(1)
    proof.set(index: 0, value: sibling)
    let proof = proof.to_dyn_array()

    assert!(merkle::verify(proof, root, leaf))
    assert!(!merkle::verify(proof, root, leaf: keccak_words([3])))
}
```

In a contract, the root would come from the application's trusted state and the
leaf would be derived from the claim using the same encoding as the tree builder.
The proof can be passed directly as a decoded ABI array.

## Text formatting and hashing

The new `core::text` module, also available as `std::text`, builds `DynString`
values with `concat`, `decimal`, `hex`, `hex_upper`, and `base64`. `concat_slice`
accepts a runtime-length slice of strings, while `TextBuilder` supports
incremental text construction that preserves the input bytes.

`DynString` gains `slice`, `from_word_prefix`, and `zeroed`, and both `Bytes` and
`DynString` now implement `Eq`. String literal escapes such as `\n`, `\t`, and
`\"` are decoded correctly instead of being kept verbatim; invalid escapes
produce source diagnostics.

For EVM-specific formatting and hashing:

- `std::evm::checksum_address` formats ERC-55 checksummed addresses.
- `std::evm::keccak_words` hashes a fixed list of words.
- `encode_packed` and `keccak_packed` write values directly at their packed
  widths, making them about four times cheaper. Custom-width Solidity integers now support packed encoding too.
- String literals longer than 31 bytes can be used as tuple parts in
  `core::keccak`, `std::abi::sol`, and `std::io::write` / `writeln` arguments.

## ABI compatibility

Message variants returning tuples with dynamic elements now encode them as a
Solidity parameter list. For example, `-> (DynString, Bytes32, Address)` matches
Solidity's `returns (string, bytes32, address)`, without an extra leading offset
for a single enclosing tuple.

Typed calls and `std::abi::sol::decode_output` use the same convention, and the
JSON ABI lists one output per tuple element. This changes the returndata of
dynamic tuple returns. Static tuples keep the same bytes; a single dynamic
return or an `#[abi]` struct is unchanged.

Generated JSON ABIs now include reachable custom errors, including errors
raised through `Result::unwrap()` and overloaded operators. Event entries
include `"anonymous": false` for strict consumers such as Foundry's Alloy parser,
and call-local memory effects alone no longer prevent a function from being
marked `pure`.

The decoder accepts dynamic bytes and strings without trailing padding while
preserving bounded reads and copies. Overflowing offsets and lengths revert
with empty data instead of arithmetic panics. Payable handlers with return
values and events with no fields also compile correctly.

## Gas, bytecode size, and compilation

`DynArray::get` now reuses the frame validation performed when the array was
constructed. Bounds checks and canonical-value validation remain in place.
In the Merkle proof benchmark reported in the changelog, this cuts gas for a
16-sibling proof by about 46% and runtime bytecode by about 28%.

Constant strings are now folded during ABI encoding instead of having their
length calculated at runtime. In the reported ERC-20 benchmark, runtime bytecode
shrinks by about 21%, and gas for `name()` drops from 3,861 to 857. These numbers
come from the individual benchmarks; the effect on other contracts depends on
how they use the affected operations.

Helpers reached from multiple `recv` arms or modules are now emitted once
instead of once per caller. The compiler also caches and shares more work in
semantic analysis, trait solving, and borrow checking.

Parsing deeply nested generic arguments is much faster. Previously, resolving
the ambiguity between generic arguments and shift operators repeatedly parsed
the same nested syntax. Reusing those results reduces a reported 12-level case
from about 96 seconds to milliseconds, including similar incomplete syntax
encountered while editing.

## Other fixes and diagnostics

A few more changes worth calling out:

- `continue` in a `for` loop now advances to the next element instead of
  revisiting the same one.
- Recursive pointer types such as `struct Node { value: u256, next: *Node }`
  now compile successfully.
- Bare function names inside an `impl` or `trait` resolve to module-level
  functions. Use `Self::name(...)` or `self.name(...)` to call an associated
  function or method; associated constants remain usable unqualified.
- Generic defaults, associated types inherited from supertraits, and generic
  arguments beginning with qualified paths resolve more reliably. Malformed
  `sol("...")` selector signatures now produce `fe check` errors.
- Integer expression literals larger than 256 bits are rejected instead of
  being silently truncated during EVM lowering.
- `core::panic_code` and the `core::panics::PANIC_*` constants expose standard
  Solidity panic codes. Out-of-bounds `core::ptr` accesses now revert with
  `Panic(0x32)` instead of `INVALID`.
- `fe test` and the contract test harness now use Osaka rules, matching the
  compiler's EVM target, so instructions such as `CLZ` execute in tests. The
  Osaka per-transaction gas cap is lifted for tests.

## Try it!

[Fe 26.4.1](https://github.com/argotorg/fe/releases/tag/v26.4.1) is available
now for Linux, macOS, and Windows and replaces 26.4.0. Let us know what you think!

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation
