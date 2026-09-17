# Fe 26.3 — Tweet thread

English tweet copy with German visual ideas. The final link points to the release post.

## 1. Release announcement

Fe 26.3 is here! 🧵

First-class memory pointers, new array and ERC-20 helpers, important compiler fixes, and foundations for source-level debugging.

Here’s what’s new ↓

**Visual:** Titelkarte „Fe 26.3“ mit drei Stichworten: Memory · Interoperability · Debugging.

## 2. First-class pointers

Fe now has first-class memory pointers: `*T`.

Allocate typed memory, read and write through dereferences, access fields, and index pointer-backed arrays.

The compiler also prevents pointer-bearing values from escaping into persistent or transient storage.

**Visual:** Codekarte mit `let p: *u256 = ptr::alloc<u256>()`, `*p = 41`, `*p += 1`.

## 3. Memory APIs

Memory APIs now distinguish read-only views from owned allocations:

• MemSlice<T> / MemSpan: read-only views
• MemBuffer: owned memory with length and capacity
• FixedMemBuffer<N>: fixed-size allocation

This replaces the previous low-level memory API.

**Visual:** Ein Speicherblock mit markierter Länge und Kapazität; darüber ein `MemSpan`, der einen lesbaren Ausschnitt zeigt.

## 4. Storage layouts

An important correctness fix: nested storage maps now receive independent inferred layout values.

Previously, distinct maps could accidentally share a salt and overwrite each other’s data.

Language-server editor hovers now also show layouts grouped by storage, transient storage, and code.

**Visual:** Schema mit zwei Maps und getrennten Speicherbereichen; alternativ ein echter Screenshot des neuen Layout-Hovers.

## 5. Dynamic arrays

Working with ABI arrays is easier:

• DynArray<T>.get(index) reads typed elements
• MemVec<T> provides mutable memory arrays
• .to_dyn_array() creates an independent ABI-encodable snapshot

MemVec’s length is set at creation; it does not grow.

**Visual:** Codekarte: `MemVec::zeroed(3)` → `.set(index: 0, value: 100)` → `.to_dyn_array()`.

## 6. Array and tuple equality

Arrays and tuples now support == and != when their elements implement Eq.

Comparisons work recursively, respect custom equality, and stop at the first mismatch.

Fixed-size arrays and tuples of up to six elements are supported, including the empty tuple.

**Visual:** Zwei kurze Vergleiche: `[1, 2, 3] == [1, 2, 3]` und `(7, true) != (7, false)`. Unterschied farbig markieren.

## 7. Dynamic fields in events

Dynamic array event fields now produce correct Solidity signatures.

A ValuesChanged event containing DynArray<u256> gets the signature:

ValuesChanged(uint256[])

Aliases and nested array types work too. Indexed dynamic fields remain unsupported.

**Visual:** Event-Definition links, kanonische Signatur und `TOPIC0 = keccak256(signature)` rechts.

## 8. Packed encoding

New packed encoding helpers:

• encode_packed builds byte payloads
• keccak_packed hashes them directly
• Packed builds payloads incrementally

There’s also eip712_digest(domain_separator: ..., struct_hash: ...) for the final EIP-712 digest.

**Visual:** Byte-Streifen: `u16` = 2 Bytes, `Address` = 20 Bytes, ohne ABI-Padding; darunter ein Pfeil zum Hash.

## 9. ERC-20 helpers

ERC-20 tokens don’t all return data the same way.

New safe_transfer, safe_transfer_from, and safe_approve helpers accept true or empty returndata, reject false and targets without code, and propagate token reverts.

**Visual:** Kleiner Entscheidungsbaum: `true` / leer mit Contract-Code → Erfolg; `false` / kein Code → Revert.

## 10. External calls

More tools for external calls:

• Address::static makes typed STATICCALLs
• encode_msg_calldata prepares selector + arguments
• call_with_default handles successful calls with empty returndata

Non-empty returndata is still decoded strictly.

**Visual:** Ablaufgrafik: Fe Message → Selector + ABI-Argumente → Contract → Return-Decoding.

## 11. Metadata rebuilds

Fe 26.2 added contract metadata. Fe 26.3 adds rebuilding from it:

fe build --from-metadata out/Token.metadata.json

The compiler reconstructs the project and uses its recorded settings—a building block for source verification and external tooling.

**Visual:** `metadata.json` → Sources + Settings → Fe Compiler → Bytecode.

## 12. Debugging foundations

Source-level debugging foundations are landing.

New developer commands track bytecode-to-source attribution and export an experimental Fe-specific ethdebug view.

Coverage is partial, APIs are unstable, and compatibility with existing ethdebug tools is not yet established.

**Visual:** Fe Source → MIR → Sonatina → EVM-Instruktion mit PC. Einige Verbindungen gestrichelt; Label „Experimental foundations“.

## 13. Compiler improvements

Compiler improvements include:

• Better trait inference and match diagnostics
• Support for functions and recv arms with >16 arguments
• Function deduplication to reduce compile time
• More useful errors where the compiler previously crashed

**Visual:** Vier schlichte Kacheln: Type inference · Wide calls · Compile time · Diagnostics.

## 14. Read the announcement

There’s more: integer square roots, new StorageBytes reads, wrapping arithmetic for Solidity integer types, and missing usize assignment operators.

Read the full announcement, including migration notes for the memory APIs:

https://blog.fe-lang.org/posts/release-26-3/

**Visual:** Abschlusskarte „Explore Fe 26.3“ mit Blog-Adresse und Fe-Logo.
