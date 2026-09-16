+++
title = "Fe 26.3.0"
date = "2026-09-16"
+++

The Fe team is happy to announce the release of Fe 26.3.0!

This release adds first-class memory pointers, a new set of memory APIs, and
standard library helpers for working with dynamic arrays, packed data, and
ERC-20 tokens. It also lays the groundwork for source-level debugging, fixes an
important contract-layout bug, and improves type inference, diagnostics, and
compilation of large projects. Highlights are below;
the full changelog is here: [v26.3.0](https://github.com/argotorg/fe/releases/tag/v26.3.0)

## First-class memory pointers

Fe now has a built-in pointer type, `*T`. Pointers support dereference reads and
writes, field access, and mutable indexing into pointer-backed arrays.

```rust
use core::ptr

#[test]
fn pointer_example() {
    let p: *u256 = ptr::alloc<u256>()
    *p = 41
    *p += 1
    assert!(*p == 42)
}
```

This replaces the `MemPtr<T>` wrapper and gives the compiler a typed
representation of memory addresses. Pointer-bearing values cannot be stored in
persistent or transient storage, including when the pointer is nested inside
another type.

There is one related parsing change: a bare `*` at the beginning of a line is
now interpreted as a dereference. If you split a multiplication across lines,
keep the `*` at the end of the preceding line.

## Memory regions and buffers

The pointer work comes with a redesign of the memory APIs used by ABI encoding,
hashing, calls, and other EVM operations. These APIs now distinguish a read-only
view from an owned allocation and track the extent of the memory region:

- `MemSlice<T>` is a read-only view over typed values in memory.
- `MemSpan` is the byte-view version, an alias for `MemSlice<u8>`.
- `MemBuffer` owns an allocation and tracks its logical length and writable capacity.
- `FixedMemBuffer<N>` keeps the allocation size in the type, making that size
  visible to the backend.

For example, an operation that reads bytes can take a `MemSpan`, while code
building a payload can use a `MemBuffer` and pass its `.span()` to the reader.

This is a breaking change for code using the previous low-level memory APIs.
`MemPtr<T>`, `core::abi::MemoryInput`, `std::evm::MemoryBytes`,
`std::evm::mem::alloc`, and the cursor-based `AbiEncoder` API have been removed.
Use `*T` for typed memory addresses, `MemSpan` for read-only byte regions, and
`MemBuffer` for owned or writable allocations. Allocation helpers now live in
`core::ptr`.

The unused `core::convert::Into<T>` trait has also been removed; use explicit
conversion APIs instead.

## Independent layouts for nested storage maps

This release fixes a critical bug in the assignment of inferred contract-layout
parameters. A type such as `StorageMap<K, V, const SALT: u256 = _>` asks the
compiler to assign a salt. Previously, repeating such a type inside a struct,
tuple, array, or other composite type could assign the same salt to distinct
maps. A write through one map could then overwrite data belonging to another.

Each structural occurrence now receives an independent inferred value. This
also applies through type aliases, nested generic arguments, and enum payloads.
Explicit values are reserved before inferred values are assigned, so mixing
explicit and inferred salts cannot accidentally collide because of declaration
order. Intentionally shared explicit values and enum overlays continue to share.

The compiler also preserves these assignments as values pass through pattern
matches, indexing, function calls, effects, and returns. Invalid or unresolved
layouts now produce diagnostics instead of partial layouts or compiler crashes.

### Layout information in the editor

Language-server hovers now show the contract layout in terms of source fields.
Hovering a contract name displays its layout grouped under Storage, Transient
Storage, and Immutable (Code); hovering a field shows just that field's entries.

The display includes explicit and inferred layout parameters, source paths and
types, and index formulas for static arrays. This makes it easier to inspect
where nested maps and other layout-parameterized fields end up.

## Dynamic array access and `MemVec`

`DynArray<T>` now supports typed element reads with `.get(index)`. The new
`std::abi::MemVec<T>` provides a mutable memory array that can be converted into
an ABI-encodable `DynArray` for contract calls, return values, and event payloads.

```rust
use std::abi::{DynArray, MemVec}

fn make_amounts() -> DynArray<u256> {
    let mut amounts: MemVec<u256> = MemVec::zeroed(3)
    amounts.set(index: 0, value: 100)
    amounts.set(index: 1, value: 200)
    amounts.set(index: 2, value: 300)
    amounts.to_dyn_array()
}

#[test]
fn array_example() {
    let amounts = make_amounts()
    assert!(amounts.get(1) == 200)
}
```

The length of a `MemVec` is chosen at creation and remains fixed; it does not
have a `push` operation. `MemVec::from_dyn_array` creates an independent mutable
copy of an existing array, and `.to_dyn_array()` creates an independent snapshot,
so later writes to the builder do not change the encoded result.

Element types must occupy one static ABI word, including integers, `Address`,
`bool`, and fixed-byte types. Reads follow Solidity ABI decoding rules, and
out-of-bounds reads or writes revert with `Panic(0x32)`.

### Dynamic arrays in events

Non-indexed dynamic array event fields now produce the correct Solidity event
signatures, including when their types use imported aliases or contain fixed-size
arrays. For example, a `ValuesChanged` event with a `DynArray<u256>` field gets
the canonical signature `ValuesChanged(uint256[])`. Previously, evaluating the
generated `TOPIC0` for these fields could crash the compiler.

Indexed dynamic fields remain unsupported and now receive a targeted diagnostic.
Failures when evaluating generated event constants also produce diagnostics.

## Array and tuple equality

Fixed-size arrays and tuples now support `==` and `!=` when their element types
implement `Eq`. Arrays compare element by element, and tuples support up to six
elements, including the empty tuple `()`.

Comparisons use each element's `Eq` implementation and stop at the first
mismatch. This also works for nested arrays and tuples, and for custom element
types without requiring them to implement `Copy`.

## Packed encoding and EIP-712 digests

`std::evm::packed` adds tightly packed encoding for integers, addresses,
booleans, strings, and byte sequences. Values are concatenated without ABI word
padding or length prefixes: a `u16` contributes two bytes and an `Address`
contributes twenty.

Use `encode_packed` to build a payload from a tuple, or `keccak_packed` when you
only need its hash. For example, hashing a pair of token addresses for a CREATE2
salt:

```rust
use std::evm::RawMem
use std::evm::packed::keccak_packed

fn pair_salt(token0: Address, token1: Address) -> u256 uses (mem: mut RawMem) {
    keccak_packed((token0, token1))
}
```

A growable `Packed` builder supports payloads assembled at runtime, with append
methods for individual value types. The module follows Solidity's
`abi.encodePacked` encoding for the supported types; non-byte arrays are not
supported.

`std::evm::crypto::eip712_digest(domain_separator: ..., struct_hash: ...)` also
provides a helper for hashing the EIP-712 prefix, domain separator, and struct
hash into the final digest.

## ERC-20 transfers and external calls

Some ERC-20 tokens return `true` from a successful transfer, while others return
no data. The new `std::evm::erc20` helpers handle both conventions:

- `safe_transfer`
- `safe_transfer_from`
- `safe_approve`

They reject `false` returns and targets without code, and propagate revert data
from the token. `safe_approve` does not reset an existing allowance to zero;
callers interacting with a token that requires this must do so explicitly.

The underlying `Call::call_with_default` and `Address::call_with_default` APIs
are available for other protocols with optional return data. A successful call
with empty returndata produces the supplied default; non-empty returndata is
still decoded strictly. Unlike the ERC-20 helpers, the general helper also
returns the default for a successful call to an address without code.

Two more additions make external calls easier:

- `Address::static` performs a typed `STATICCALL`, forwards the available gas,
  and propagates the callee's revert data on failure.
- `std::evm::encode_msg_calldata` encodes a message selector and its arguments
  into memory for use with low-level calls.

## Rebuilding from contract metadata

Fe 26.2 added Solidity-standard contract metadata. Fe 26.3 adds the other side
of that workflow:

```sh
fe build --from-metadata out/Token.metadata.json
```

The compiler reconstructs the recorded project in a temporary directory and
builds the contract selected by `settings.compilationTarget`, using the optimizer
level recorded in the metadata. The JSON can also be read from stdin with
`--from-metadata -`. Artifacts go to `--out-dir`, defaulting to `./out`.

This gives source verifiers and external toolchains a way to rebuild a contract
from one self-contained JSON document. `--contract` can override the selected
contract, and an explicit `-O` overrides the recorded optimizer setting with a
warning. A compiler version mismatch also warns rather than stopping the build;
matching the original bytecode still requires the original compiler and settings.

## Foundations for source-level debugging

Fe 26.3 introduces compiler infrastructure for connecting emitted EVM bytecode
back to Fe source code, along with an experimental ethdebug export. This is
foundational work toward source-level debugging; the end-user workflow is still
being developed.

The compiler tracks source attribution through MIR and the Sonatina backend to
individual bytecode instructions at their actual program-counter offsets, for
both contract creation and runtime code. Instructions are classified as
source-mapped, ambiguous, synthetic, or unmapped. Source context is attached only
when the recorded compiler facts establish a unique exact mapping, so gaps and
ambiguities remain visible. Coverage is partial: these mappings do not capture
every contributing source expression or the full history of optimizations.

The new `fe dev trace emit` command compiles a Fe file or ingot and writes these
compiler facts as a validated JSONL stream. `fe dev debug emit --format ethdebug`
then exports an instruction/source view from that stream, prints an attribution
summary, and can write additional origin and confidence details for tooling
experiments.

For now, the export uses a Fe-specific experimental schema. Compatibility with
existing ethdebug consumers has not been established, and the formats and
commands are not stable public APIs. Variable locations are not yet available,
and trace generation is separate from ordinary build and test execution, so the
output is not yet tied to the exact artifact executed by a failing test. Further
integration and tooling work is needed to turn this into a polished debugging
experience.

## Type inference and diagnostics

Trait bounds on generic calls are now solved at the call site before the return
type is checked against its context. This fixes cases such as `Option::map`
where using the result later in the same function previously required a redundant
type annotation. Method selection also handles associated-type projection bounds
and competing blanket implementations more reliably.

Internally, trait resolution now uses `tablesolve`, and pattern coverage checking
uses `matchcov`. The latter catches previously missed unreachable match arms,
allows empty matches over empty enums, and reports a representative missing case
when a match is not exhaustive.

Message declarations now check that `sol("...")` selector signatures match their
fields in both argument count and ABI types, even when the build does not emit
ABI JSON. Errors point at the declaration or offending field and suggest the
corresponding standard-library type where possible.

Several cases that previously crashed the compiler now produce diagnostics or
compile correctly, including unsupported macro calls, events with many fields,
and short string literals inside aggregate constants. Mutable owned arrays,
structs, and enums also compile correctly in cases that previously produced
internal carrier-mismatch errors. A `recv` block that names a file module
instead of a message module now reports a diagnostic explaining what is expected,
rather than crashing the compiler.

Indexing an empty array nested inside another array, tuple, struct, or enum
variant now performs the expected bounds-check revert instead of crashing the
compiler.

## Compilation and standard library improvements

Functions are now deduplicated in MIR after monomorphization, reducing compile
time for large projects. Runtime layouts are also deduplicated structurally, and
library modules no longer produce duplicate ingot main objects when building
projects with dependencies.

The Sonatina backend now supports functions and `recv` arms with more than
16 arguments, removing a compilation limitation for contracts with large
message signatures and internal calls with many parameters.

A few more improvements worth calling out:

- `core::num::isqrt` computes the integer square root of a `u256`, rounded down,
  using a fixed number of Newton iterations.
- `StorageBytes::to_memory` copies stored bytes into memory without ending the
  contract call, allowing further processing such as hashing or deployment.
  `StorageBytes::word_at` reads individual payload words.
- Solidity integer wrapper types now support wrapping arithmetic operations.
- `usize` now implements the missing shift and bitwise assignment operators:
  `<<=`, `>>=`, `&=`, `|=`, and `^=`.
- Runtime ABI argument-size validation has been aligned with Solidity.
- Clean builds no longer depend on Tree-sitter parser generation order, and the
  bundled grammar handles chained `||` conditions consistently with the compiler.

## Try it!

Fe 26.3.0 is available now for Linux, macOS, and Windows. Let us know what you
think!

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation
