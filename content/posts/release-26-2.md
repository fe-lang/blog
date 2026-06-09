+++
title = "Fe 26.2.0"
date = "2026-06-25"
+++

The Fe team is happy to announce the release of Fe 26.2.0!

This release is focused on gas and bytecode-size optimizations, along with some 
language, standard library, and tooling improvements. Highlights are below; the full changelog is
here: [v26.2.0](https://github.com/argotorg/fe/releases/tag/v26.2.0)

The motivating test cases for many of the optimizations are Fe ports
of the Ethereum beacon deposit contract and the Uniswap v3 core contracts.
Gas and bytecode size are quite a bit better than in previous releases.
The deposit contract can be seen here: [deposit_contract.fe](https://fe-lang.org/examples/deposit-contract/).
Gas and bytecode size comparison with the solidity implementation are below
(fe -O2 vs solc --via-IR).

```text
bytecode size      fe      solc      fe vs solc
-----------------------------------------------
init             2562      3082      -520 (-16.9%)
runtime          2478      2844      -366 (-12.9%)

call gas                         fe      solc      fe vs solc
------------------------------------------------------------
deposit#0                     79719     81089    -1370 (-1.7%)
deposit#1                     65088     66629    -1541 (-2.3%)
deposit#2                     45507     46877    -1370 (-2.9%)
get_deposit_root(after#2)    102985    109170    -6185 (-5.7%)
get_deposit_count(after#2)    23616     24099     -483 (-2.0%)
```

## Immutable contract fields

Fe now supports Solidity-style immutable contract fields. These are set during contract
initialization and never change during the lifetime of the contract. The values are appended to the end of the runtime bytecode, and read at runtime with a `CODECOPY` operation, which is much cheaper than storage access.

```rust
pub contract Token uses (ctx: Ctx) {
    // Immutable: written once during init, embedded in the contract code
    owner: Address

    // Mutable: lives in storage
    mut store: TokenStore

    init(initial_supply: u256) uses (ctx, mut owner, mut store) {
        owner = ctx.caller()
        store.total_supply = initial_supply
        store.balances.set(key: ctx.caller(), value: initial_supply)
    }

    recv TokenMsg {
        Owner -> Address uses (owner) { 
            owner 
        }
        TotalSupply -> u256 uses (store) { 
            store.total_supply 
        }
        BalanceOf { account } -> u256 uses (store) { 
            store.balances.get(key: account) 
        }
    }
}
```

Note that an immutable field is bound as a `mut` effect in the `init` block (`uses (mut owner)`).
Immutable fields must be initialized in `init`; failure to do so is a compile-time error.

## `assert!` built-in

Fe now has an `assert!` built-in pseudo-macro:

```rust
fn validate_pubkey_len(pubkey_len: usize) {
    assert!(pubkey_len == 48, "invalid pubkey length")
}
```

`assert!(condition)` reverts with Solidity-compatible `Panic(0x01)` when the
condition is false. `assert!(condition, "message")` reverts with
Solidity-compatible `Error(string)` data, matching the shape tools already
understand from Solidity's `require`.

This functionality was previously implemented in the standard library as `assert` and
`assert_msg` functions; however, calling a normal function always evaluates its arguments
and this lead to unnecessary gas usage on the non-error path. Making this a compiler built-in
allows us only build the error string on error path. In rust, this would be accomplished with
a macro; Fe doesn't (yet?) have macros.

`assert!` also works in `const fn`: if an assertion fails at compile time, the compiler
reports the failing assertion and includes the message when one was provided.

## Associated `const` items in `impl` blocks

Inherent `impl` blocks can now define associated `const` items.

```rust
pub struct Packed<const BITS: u256> {}

impl<const BITS: u256> Packed<BITS> {
    const LANES: u256 = 256 / BITS
    const LANE_MASK: u256 = (1 << BITS) - 1

    pub fn lanes(self) -> u256 {
        Self::LANES
    }
}
```

Inherent consts take precedence over trait consts of the same name, 
with the trait const still reachable via a qualified path like
`<Foo as SomeTrait>::X`.

## Optimization levels

The `fe` CLI now defaults to the `-O1` optimization level. This gives
considerably faster compile times for large projects, with little loss in
bytecode quality relative to `-O2`.

Previously, `-O1` and `-O2` were effectively the same. Now `-O1` uses a cheaper
stack-shuffling search, while still running the full optimization pipeline.
This gets close to `-O2` gas and bytecode size while substantially reducing
compile time for large projects. `-O2` keeps the more expensive exact stack-shuffling 
search. `-O0` is now much faster because it skips the main optimizer and uses a greedy
heuristic for stack shuffling.

## Machine EVM lowering

Sonatina's EVM backend now lowers through a lower-level "machine EVM"
instruction set before final bytecode emission. Fe generates high-level Sonatina
IR with full type information, including struct, enum, and array types and operations.
This representation is optimized, then lowered to the low-level IR, which is 
optimized again by the same passes.

Running the optimizer on both representations gives the compiler
more room to clean up stack use, memory use, and repeated generated code after
the main pipeline has already run. The bytecode and memory improvements below
mostly fall out of this two-stage approach.

## EVM bytecode improvements

### PUSH shrinking

Large EVM constants are now emitted in shorter forms when a small runtime
operation can replace a much larger literal. This is especially useful for ABI
selectors and masks, which appear frequently in generated wrapper code, error
paths, and integer cleanup logic.

For example, a selector stored in the high four bytes of an ABI word, previously
pushed as a 32-byte literal:

```text
PUSH32 0x4e487b7100000000000000000000000000000000000000000000000000000000
```

is now emitted as a short selector plus a shift:

```text
PUSH4 0x4e487b71
PUSH1 0xe0
SHL
```

A similar transformation applies to low-bit masks:

```text
PUSH20 0xffffffffffffffffffffffffffffffffffffffff
```

becomes:

```text
PUSH0
NOT
PUSH1 0x60
SHR
```

These transformations trade a little runtime gas for reduced bytecode size, and
are currently applied at all optimization levels. In a future release this will
depend on the optimization level, with `-Os` most aggressively saving bytes and
`-O2` sacrificing bytes for runtime gas.

### Code and data deduplication

Sonatina now deduplicates function bodies that lower to identical EVM bytecode
*after* optimization. Previously, two functions were only considered the same
when their Sonatina IR was identical, which left some bloat when distinct
functions optimized down to the same bytecode. The backend also removes repeated
constant-only helper parameters when every private call passes the same value,
and deduplicates terminal return/revert code, which shrinks error-handling paths.

## Memory optimizations

Several improvements focus on temporary memory:

- Private temporary buffers can be placed in fixed scratch slots when their
  lifetimes don't overlap.
- Return and revert payloads can be built at fixed addresses instead of going
  through the heap allocator.
- Known free-pointer bounds are reused across internal calls, avoiding redundant
  allocator setup.
- Unnecessary overflow checks are dropped for offsets inside statically sized EVM
  allocations.

This matters most in code with many generated helpers, ABI paths, and error
payloads. In the checked-in differential deposit-contract benchmark, Fe's deposit
calls are now slightly cheaper than the best Solidity variant in the comparison
run, and `get_deposit_root` is noticeably cheaper.

## Const data and large arrays

Fe 26.2 benefits from several improvements to const array handling in Sonatina.

Fe lowers constant aggregates as shared const references in Sonatina IR, and 
Sonatina decides how to materialize the const values.

Previously, a const array was naively stored in each function that used it. 
Now, these are stored as a single bytecode data region, dramatically reducing
bytecode size for large lookup tables that are used in several places. Static array
access can be optimized down to a `PUSH` of the constant value. Some dynamic uses of const 
arrays can be optimized as well. For example, `[10, 20, 30, 40]` indexed by `i`
in a loop compiles to `i*10 + 10` with no const region.

Sonatina will also deduplicate const data, and coalesce `CODECOPY`s of individual elements
into larger region copies where it's benefitial.

## ABI encode/decode efficiency

The std library implementation of Solidity-compatible calldata ABI encoding/decoding 
is now much more efficient. On the receive-side, we now avoid redundant memory copies 
before decoding. Many small helper functions in the implementation have been marked `#[inline(always)]`,
which avoids internal call overhead on hot paths. (Ideally Sonatina would inline these
automatically; the inlining heuristics need more work.)

A couple related fixes here too: encoding for payloads with multiple dynamic fields, and
encoding of negative signed integers narrower than 256 bits was incorrect.

## `#[must_use]` and fallible precompiles

This release adds support for a rust-like `#[must_use]` attribute, which can be attached
to any type definition or function. If a value of a `must_use` type or the return value
of a `must_use` function isn't used, it will result in compile-time error:

```text
error[8-0082]: unused value of type `Result<PrecompileError, Option<u256>>`
  ┌─ src/verify.fe:9:5
  │
9 │     ecrecover(hash: hash, v: v, r: r, s: s)
  │     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ use this value or explicitly discard it with `let _ = ...`
  │
  = this type is marked `#[must_use]`
```

This pairs with a change to the EVM crypto precompiles. `std::evm::crypto` now includes wrapper functions
for all crypto-related precompiles (`ecrecover`, `sha256`, `ripemd160`, identity, Blake2F, KZG
point evaluation, BLS12-381, and P-256); these wrappers return
`Result<PrecompileError, T>` instead of reverting when the precompile
call fails. `Result` is now marked `#[must_use]`, and thus can't be accidentally ignored.
Calling `.unwrap()` will revert if the `Result` is an `Err`.

## Standard library additions

- `Option::ok_or` and `Option::ok_or_else` (mirroring Rust's API).
  This can be combined with `Result::unwrap` to attach a a typed error to an `Option` unwrap 
  so reverts carry meaningful Solidity-compatible error data instead of `Panic(0x01)`.
- `StorageMap` keys now support all primitive integer types (`u8`–`u128`,
  `usize`, `i8`–`i256`, `isize`) and `bool`, in addition to `u256`, `Address`,
  and tuples.
- `core::num` gains the `Bounded` trait (`T::min()`/`T::max()` as `const fn`),
  and the `Abs` / `UnsignedAbs` traits for signed-magnitude operations with
  explicit stances on the `T::MIN` edge case.
- New `String<N>` utilities for concatenation, and equality in both const and runtime code.
- Lossless `bool`-to-integer casts with `as` are now allowed. This is useful for hand-optimized branchless
  code.

## Tooling

### Contract metadata
`fe build --emit metadata` writes a Solidity-standard `metadata.json` 
for each contract. This is used by verifiers like [Sourcify](https://sourcify.dev) to
reproduce the build and verify the deployed bytecode.

### `fe doc` improvements
- `msg` variants are now shown on the parent `msg` page
- contract docs now have init and message-handler sections
- `#[test]` functions are now hidden from generated docs by default (restore them with `--include-tests`). 
- The doc viewer now exposes CSS variables for fonts, weights, and layout, for easy retheming.

## Try it!

Fe 26.2.0 is available now for Linux, macOS, and Windows. Let us know what you
think!

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation
