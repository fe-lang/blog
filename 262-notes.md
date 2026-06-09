## 26.2 (2026-06-09)

### Features

- Added `Option::ok_or` and `Option::ok_or_else` to `core`, mirroring Rust's API, plus a `Panic::from(code)` shorthand constructor. Combined with `Result::unwrap`, this lets users attach a typed error value (e.g. `Panic::from(POP_EMPTY)`) to an Option-unwrap so reverts carry meaningful Solidity-compatible selectors instead of always landing on `Panic(0x01)`. ([#1430](https://github.com/argotorg/fe/issues/1430))

- `StorageMap<K, V>` now accepts every primitive integer type (`u8`–`u128`, `usize`, `i8`–`i256`, `isize`) and `bool` as a key, in addition to the previously supported `u256`, `Address`, and tuples. The new `StorageKey` impls left-pad each key to 32 bytes via `WordRepr::to_word()`, so slot derivation matches Solidity's `mapping(intN/uintN/bool => V)` convention exactly. Useful for storage layouts that want to pack indices into a single slot (e.g. `mapping(uint128 => V)` queues). ([#1431](https://github.com/argotorg/fe/issues/1431))

- Improved optimization options for the default Sonatina backend:
  - `-O1`/`--optimize 1` is now distinct from `-O2` and is the default optimization level. It keeps Sonatina's optimization pipeline enabled while using lower exact-search caps for stack shuffling; usually getting close to `-O2` gas and bytecode while substantially reducing compile time.
  - `-O0`/`--optimize 0` now and disables the stack shuffling exact solver entirely in favor of a greedy heuristic, making unoptimized builds much faster.
  ([#1435](https://github.com/argotorg/fe/issues/1435))

- Added core `String<N>` utilities for fixed-width byte round-trips, effective byte length, concatenation, and equality in const and runtime code. ([#1437](https://github.com/argotorg/fe/issues/1437))

- Lossless `bool` to integer casts with `as` are now allowed. ([#1445](https://github.com/argotorg/fe/issues/1445))

- Exposed selected raw EVM operations through `std::evm::ops`, including byte/sign-extension, balance/code inspection, gas price, and blob fee/hash reads. ([#1453](https://github.com/argotorg/fe/issues/1453))

- Precompiles:
    - `std::evm::crypto` precompile wrappers now `Result<PrecompileError, T>`
    instead of reverting on precompile call failure.
    - Added typed wrappers for the remaining EVM crypto precompiles, including
    RIPEMD-160, identity, Blake2F, KZG point evaluation, BLS12-381 operations, and
    P-256 verification.
    - `ecrecover` now rejects non-canonical secp256k1 signatures before returning
    a recovered address.
    - added `ecrecover_raw` which does not perform canonical signature checks. ([#1468](https://github.com/argotorg/fe/issues/1468))

- Added marker-only `#[must_use]` support for functions, structs, and enums, and marked `core::result::Result` as must-use so ignored fallible results are diagnosed unless explicitly discarded with `let _ = ...`. ([#1468](https://github.com/argotorg/fe/issues/1468))

- Added `assert!` builtin, e.g. `assert!(ok)`. Takes an optional second string
  literal argument: `assert!(ok, "something's not ok")`. Assertion failure results
  in a revert, with Solidity-compatible `Error(string)` payload. `assert!` can
  also be used in `const fn`s at compile time; assertion failure results in a
  compile-time failure. ([#1471](https://github.com/argotorg/fe/issues/1471))

- Added the `Abs` and `UnsignedAbs` traits in `core::num`, providing magnitude operations as `const fn` on all signed integer types. `Abs` bundles `abs`, `checked_abs`, `wrapping_abs`, `saturating_abs`, and `overflowing_abs`, each taking a different stance on the asymmetric `T::MIN` edge case. `UnsignedAbs::unsigned_abs()` returns the magnitude in the unsigned type of the same width — handling `T::MIN` without overflow. ([#1474](https://github.com/argotorg/fe/issues/1474))

- Added the `Bounded` trait in `core::num`, exposing inclusive numeric type bounds as `T::min()` and `T::max()` `const fn` methods on all primitive integer types. ([#1474](https://github.com/argotorg/fe/issues/1474))

### Bugfixes

- Fixed `fe test` output so failure details are printed immediately after the corresponding failed test status when tests run in parallel. ([#1420](https://github.com/argotorg/fe/issues/1420))

- Fixed a compiler panic when generic associated constants were used in const expressions before their concrete types were known. ([#1429](https://github.com/argotorg/fe/issues/1429))

- Fixed a compiler panic when code_region_len or code_region_offset was called on an unresolved generic contract runtime parameter. ([#1429](https://github.com/argotorg/fe/issues/1429))

- Fixed Sonatina ABI encoding and decoding for negative signed integers narrower than 256 bits. ([#1434](https://github.com/argotorg/fe/issues/1434))

- Sonatina:
  - Fixed EVM encoded-pointer provenance across calls and memory operations, with more precise escape summaries for i256 pointer carriers, aggregates, malloc-derived pointers, and local/argument/nonlocal storage. This also improves memory-planning performance by avoiding unnecessarily conservative escape assumptions.
  - Fixed GVN value-phi materialization so cached/generated value phis are rejected unless they cover the currently reachable predecessors.
  - Improved stackify spill slot reuse logic. This fixes a bug where a scratch slot could be reused for values that overlap during phi/control-flow transitions.

  ([#1435](https://github.com/argotorg/fe/issues/1435))

- Fixed ABI encoding for `evm.call` message payloads with multiple dynamic fields, and for dynamic custom error payloads. ([#1439](https://github.com/argotorg/fe/issues/1439))

- Fixed expression-context `&&` and `||` lowering so right-hand side expressions are only evaluated when short-circuiting requires them. ([#1447](https://github.com/argotorg/fe/issues/1447))

- Fixed compiler panic when lowering zero-sized effect types. ([#1449](https://github.com/argotorg/fe/issues/1449))

- Allowed blanket implementations of external traits when the implementor is a type parameter directly bounded by a local trait. ([#1450](https://github.com/argotorg/fe/issues/1450))

- Fixed calls through projected effect providers, such as `with (store.map)`, so nested calls preserve the projected provider's concrete target type. ([#1459](https://github.com/argotorg/fe/issues/1459))

- Sonatina:
    - Fix unchecked signed EVM division and remainder for narrow signed integer types.
    - Fix EVM codegen for spilled phi values so control-flow joins do not let one edge's object storage clobber another edge's phi source. ([#1470](https://github.com/argotorg/fe/issues/1470))

- Fixed the parser rejecting multiple items on the same line inside `impl`, `trait`, and `extern` blocks. The tree-sitter grammar already allowed `impl Foo for Bar { fn a() {}  fn b() {} }`, but the main parser required a newline between items. ([#1475](https://github.com/argotorg/fe/issues/1475))

- Fixed compiler panics when tuple type aliases were used as event or custom error fields. ([#1481](https://github.com/argotorg/fe/issues/1481))

### Performance improvements

- Fe:
    - Lower named aggregate constants as Sonatina const refs.
    - Only emit Sonatina data regions for constants that are explicitly used as code regions.
    - Avoid duplicated const data in generated bytecode for large const arrays.
    - Improve runtime lowering for const-backed local borrows.
    - Avoid emitting real globals/data entries for zero-sized aggregate constants.
    - Lower view aggregate arguments in a representation-flexible way so the compiler can avoid unnecessary aggregate allocation and copying.
  Sonatina:
    - Compact and specialize constref loads.
    - Deduplicate const data.
    - Coalesce adjacent const loads.
    - Prune dead const sections and functions.
    - Reduce compile-time blowups for large const arrays. ([#1433](https://github.com/argotorg/fe/issues/1433))
- Sonatina:
  - Improved stack shuffling performance via cache improvements and short-circuiting trivial operand-prep cases.
  - Improved memory placement performance.

  ([#1435](https://github.com/argotorg/fe/issues/1435))
- Improved Solidity ABI encoding and decoding performance for dynamic payloads by avoiding redundant memory copies and adding faster paths for canonical dynamic arrays. ([#1440](https://github.com/argotorg/fe/issues/1440))
- Calldata ABI decode optimizations:
    - Decode contract `recv` arguments directly from calldata instead of first copying the payload into memory.
    - Inline hot ABI decoding helpers and storage map key paths to reduce generated wrapper overhead. ([#1448](https://github.com/argotorg/fe/issues/1448))
    - 
- Sonatina:
    - EVM lowering now goes via a "machine EVM" instruction set, with additional
      optimizations and better stack and memory management.
    - Improve inlining for small specialized helpers, especially helpers with known callsite arguments or scalarizable object arguments.
    - Sink pure computations into the branch or join block where their results are used, reducing unnecessary work and stack pressure. ([#1470](https://github.com/argotorg/fe/issues/1470))
- Fe:
    - Avoid object-backed runtime storage for read-only owned aggregates, tuple destructuring, and read-only aggregate helper calls.
    - Construct runtime aggregate values directly.
  Sonatina:
    - Account for scalarizable aggregate inserts, extracts, and returns when deciding whether to inline small helpers.
    - Copy aggregate insert-value webs directly to memory during aggregate legalization instead of materializing source aggregate slots.
    - Skip zero-sized aggregate leaf memory operations during aggregate legalization. ([#1483](https://github.com/argotorg/fe/issues/1483))
- Sonatina:
    - Keep explicit `inline(never)` annotations on generated const-data helper variants, preserving source-level code-size controls.
    - Emit large EVM constants in shorter forms when a small runtime operation can replace a much larger literal.
    - Remove duplicate private helper bodies after EVM lowering when they compile to identical bytecode.
    - Remove repeated constant-only helper parameters when every private call passes the same value.
    - Drop unnecessary overflow checks for offsets inside statically sized EVM memory allocations.
    - Deduplicate terminal EVM return/revert code.
    - Replace static const object initialization with direct scalar values where possible.
    - Reuse fixed scratch slots for private temporary EVM buffers whose lifetimes do not overlap.
    - Reuse known EVM free-pointer bounds across internal calls to avoid redundant allocator setup.
    - Build private return/revert payload buffers at fixed addresses instead of routing them through the heap allocator. ([#1488](https://github.com/argotorg/fe/issues/1488))
