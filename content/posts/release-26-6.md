+++
title = "Fe 26.6.0"
date = "2026-11-10"
+++

<!-- Editorial note: release-day copy, based on the v26.6.0 tag
(5b3f96af2ab10df11bf847551f4b81d1fe481110, 2026-11-10), compared with v26.5.1.
All Fe examples were checked with a `--profile dist --features fe/cranelift`
build of that commit; the native examples were built and run on x86-64 Linux.
The "Performance" numbers are taken from the release notes. Confirm the
platform artifacts and remove draft status before publishing. -->

The Fe team is happy to announce the release of Fe 26.6.0!

With 26.5 we promised big improvements to the native backend, and this
release delivers them. Native Fe programs can now print, read their arguments,
work with files, run other programs, read the clock, and call into C or be
called from it. Fe also gains destructors, so memory owners free what they
hold, and a `HashMap` in the prelude. On the EVM, contract fields now pack
into shared storage slots like Solidity state variables, and invalid array
indices and enum tags revert with Solidity's panic codes. An experimental
WebAssembly backend rounds off the release.

Several of these changes are breaking, including storage layout changes; the
[upgrade notes](#upgrading-from-26-5) at the end summarize what existing code
needs. Highlights are below; the full changelog is here:
[v26.6.0](https://github.com/argotorg/fe/releases/tag/v26.6.0)

## Native programs

Native programs now get their I/O as effects, in the same way that contracts
get storage and calls. On a native target, a test or a top-level `pub fn main`
takes its effects from the new root effect `std::native::Host`, so `main`
simply lists what it needs in its `uses` clause. Here is a small program that
counts the words in a file:

```rust
use std::abi::DynString
use std::env::Args
use std::fs::Fs
use std::io::Stdout

pub fn main() -> i32 uses (out: mut Stdout, args: Args, fs: Fs) {
    let text = match fs.read(args.get(1)) {
        Result::Ok(text) => text,
        Result::Err(error) => {
            println!("cannot read ", args.get(1), ": ", error)
            return 1
        }
    }

    var counts = HashMap<DynString, u256>::new()
    for line in text.span().lines() {
        for word in line.split(b' ') {
            if word.len() > 0 {
                counts.get_or_insert(DynString::from_payload(source: word), 0) += 1
            }
        }
    }

    for (ref word, count) in counts.entries() {
        println!(word, ": ", count)
    }
    0
}
```

```sh
fe build --backend native --out-dir out wordcount.fe
./out/wordcount notes.txt
```

A function that doesn't list `Fs` in its `uses` clause can't touch the file
system, and a function that only lists `fs: Fs` can read files but not write
them. The same goes for the other new capabilities:

- `std::io` provides `Stdout`, `Stderr` and `Stdin`, along with the macros
  `print!`, `println!`, `eprint!`, `eprintln!` and `format!`. `write!` and
  `writeln!` append to an existing `MemBuffer`, and `StdinReader` reads
  standard input a byte or a line at a time.
- `std::env` provides `Args` and `Env`, and `std::process` provides `Exit`.
- `std::fs` reads, writes and appends to files, creates directories, and
  lists them. Failures return a `std::io::Error` that carries the host's
  `errno` and displays as the host's message, as in the example above.
- `std::process` runs other programs. A `Command` sets the arguments,
  environment, directory, standard streams, and a timeout:
  `proc.output(Command::new("git").arg("status").stdout(Redirect::Capture))`.
  The resulting `Output` also reports the child's CPU time and peak memory.
- `std::time` reads the monotonic clock and the wall clock.

`fs`, `process` and `time` are available on Linux and macOS. A program that
asks for an effect its target doesn't provide, such as `Evm` on a native
target or `Stdout` on the EVM, is now a type error. `pub fn main()` may also
return nothing, in which case it exits with 0.

Panics in native programs now print a message on stderr, such as
`panicked: arithmetic overflow` or the message of an `assert!`, after
flushing any output written before them. In 26.5 they stopped with a bare
`SIGILL`. Native `fe test` also supports `#[test(should_revert)]` now.

### Working with C

Fe and C code can now be linked together in both directions. A Fe `extern`
function can be implemented in C or Rust and linked into an executable with
`--link <PATH>` or `--link-lib <NAME>`. Calling an `extern` function requires
an `unsafe` block, since nothing checks what foreign code does.

Going the other way, `#[unsafe(export)]` makes a native build define a
function with the C calling convention, and `--emit staticlib` writes a static
library that C and Rust programs link like any other:

```rust
#[unsafe(export)]
pub fn fe_gcd(_ a: u64, _ b: u64) -> u64 {
    var x = a
    var y = b
    while y != 0 {
        let t = y
        y = x % y
        x = t
    }
    x
}
```

```c
#include <stdint.h>
#include <stdio.h>

uint64_t fe_gcd(uint64_t a, uint64_t b);

int main(void) {
    printf("%llu\n", (unsigned long long)fe_gcd(1071, 462));
    return 0;
}
```

```sh
fe build --backend native --emit staticlib --out-dir out gcd.fe
cc main.c out/libgcd.a -o gcd
./gcd   # prints 21
```

`--emit object` writes a plain object file instead.

### Conditional compilation and project targets

Items and modules can be compiled conditionally with `#[cfg(..)]`, using
`target = "evm"` or `"native"`, `target_os = "linux"` or `"macos"`, and
`target_family = "unix"`:

```rust
#[cfg(target_os = "linux")]
fn platform() -> String<8> { "linux" }

#[cfg(target_os = "macos")]
fn platform() -> String<8> { "macos" }

#[cfg(target = "evm")]
fn platform() -> String<8> { "evm" }
```

`#![cfg(..)]` at the top of a module applies to the whole module. A project
can also set its target in `fe.toml` with `target = "native"`, so that
`fe check`, `fe build`, `fe test` and the language server use it without
passing `--backend` every time.

### 64-bit `usize`

On native targets, including SP1, `usize`, `isize` and pointers are now 64
bits wide. Before, they were 256-bit words, so every index, length and pointer
took four machine words. A loop counting in `usize` now runs about 30 times
faster, and a `MemVec` scan about 45 times faster.

As a result, `as` casts must now be lossless on every target: `u32 as usize`
and `usize as u256` still work, but `u256 as usize` or `usize as u64` are
rejected. Use `downcast()`, `downcast_saturate()` or `downcast_unchecked()`
instead.

## Destructors and owned memory

Owned values are now destroyed exactly once, when their owner gives them up:
at the end of a scope, when they are overwritten, or when a partial move
leaves fields behind. `MemVec`, `MemArray`, `MemBuffer` and `FixedMemBuffer`
free their allocations and destroy their elements, so on native targets
memory no longer leaks and there is no `release` call to forget:

```rust
use core::MemVec

struct Tree {
    value: u256,
    children: MemVec<Tree>,
}

fn leaf(_ value: u256) -> Tree {
    Tree { value, children: MemVec::new() }
}

fn sum(_ tree: Tree) -> u256 {
    var total = tree.value
    for ref child in tree.children {
        total += sum(child)
    }
    total
}

#[test]
fn owned_trees() {
    var root = leaf(1)
    var branch = leaf(2)
    branch.children.push(leaf(3))
    root.children.push(branch)
    root.children.push(leaf(4))
    assert!(sum(root) == 10)
    // `root` and every node it holds are freed here.
}
```

As the example shows, a type can also contain itself through a generic type
that stores its argument behind a pointer, such as `MemVec<Tree>`. The new
`core::ptr::Box<T>` holds a single value in its own allocation.

A type can release other resources in a `core::ops::Drop` implementation:

```rust
use core::ops::Drop

extern {
    fn close(_ fd: i32) -> i32
}

struct File {
    fd: i32,
}

impl Drop for File {
    fn drop(own self) {
        let _ = unsafe { close(self.fd) }
    }
}
```

`core::mem::drop` destroys a value early, and `core::mem::forget` gives it up
without destroying it. Operations that allocate gain fallible forms such as
`MemVec::try_push`, `try_reserve` and `MemBuffer::try_new`.

`DynString`, `Bytes` and `DynArray` now own their allocations too. They are no
longer `Copy`, so use `clone()` to get a second value, or a view parameter to
read one without moving it. The
[destruction guide](https://github.com/argotorg/fe/blob/master/docs/language/destruction.md)
covers the rules in detail.

## `HashMap` and text

`core::map::HashMap<K, V>` is a hash table in the prelude that owns its keys
and values. `get` gives the value in place, `insert` and `remove` return the
old value, and `get_or_insert` gives the entry's value for update, as in
`counts.get_or_insert(word, 0) += 1` above. Lookups take any key type that the
map's key compares with, so a map with `DynString` keys can be queried with a
string literal or a span. A `for` loop visits the values, and `keys()` and
`entries()` loop over keys and `(key, value)` pairs.

Text processing has improved a lot as well. `MemSpan` gains `starts_with`,
`ends_with`, `index_of`, `trim`, `split` and `lines`, and byte literals such
as `b','` are `u8` values. The `core::text` parsers accept any text type,
including process arguments, so `parse_uint(args.get(1))` parses an argument
without copying it. Spans, buffers and arguments compare with strings, so
`args.get(1) == "serve"` just works.

```rust
use core::fixed::Wad
use core::hash::sha256_word
use core::text::decode_hex
use std::abi::DynString

#[test]
fn text_and_hashing() {
    let price = Wad::parse("1.25").unwrap()
    let total = price * Wad::from_int(3)
    assert!(format!(total) == "3.75")

    let bytes = decode_hex("0x00ff").unwrap()
    assert!(bytes.len() == 2)

    let row: DynString = "alice, 30, berlin"
    var fields: usize = 0
    for field in row.span().split(", ") {
        fields += 1
    }
    assert!(fields == 3)
    assert!(row.span().starts_with("alice"))

    let abc: DynString = "abc"
    assert!(sha256_word(abc.span()) == 0xba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad)
}
```

The example also shows other new pieces of the standard library:

- `core::hash` provides streaming Keccak-256 and SHA-256 that hash borrowed
  bytes without allocating, on every target. On the EVM,
  `std::evm::crypto::sha256` still uses the cheaper precompile.
- `UFixed::parse` and `Fixed::parse` read decimal text, and both types
  implement `Display`, writing the shortest exact text.
- `core::text::decode_hex` decodes hex with or without a `0x` prefix.

Also new: `MemSlice`, `MemArray` and `MemVec` have a `sort` method for
elements of any `Ord` type, so a `MemVec<DynString>` can be sorted, and text
is ordered as text. `MemSlice::as_chunks<N>()` views a slice as fixed-size
arrays, `MemVec::swap_remove` removes an element in constant time, and
`core::num` has generic byte order conversions and `leading_zeros` and
`trailing_zeros` for every integer width.

## Packed contract fields

Consecutive contract fields that are narrower than a slot now share storage
slots, the way Solidity packs state variables:

```rust
use std::abi::sol
use std::evm::{Address, Ctx}

msg TokenMsg {
    #[selector = sol("pause()")]
    Pause,
}

pub contract Token {
    // These three fields share one storage slot, as in Solidity.
    mut owner: Address,
    mut paused: bool,
    mut decimals: u8,
    mut total_supply: u256,

    recv TokenMsg {
        Pause uses (ctx: Ctx, owner, mut paused) {
            assert!(ctx.caller() == owner)
            paused = true
        }
    }
}
```

A packed field is read and written in place, leaving the rest of its slot
alone. Inside structs, tuples and map entries, Solidity value types now pack
as well: `Address` takes 20 bytes, `FixedBytes<N>` takes `N`, odd-width
integers such as `Uint24` take their width, and a struct with a single field
packs like that field. `struct Rec { owner: Address, flag: bool, stamp: u64 }`
takes one slot, as it does in Solidity.

Note that this moves existing fields to new slots and offsets, so a contract
compiled with 26.6 doesn't share a storage layout with the same source
compiled by 26.5. The same is true for `StoragePackedArray`, which could write
outside the array for very large indices. It now places its words like
Solady's `LibMap` and OpenZeppelin's `BitMaps`.

## Solidity panic codes

More failures now revert with the same panic codes as Solidity, so tools and
callers can tell them apart:

- An out-of-range array index reverts with `Panic(0x32)` instead of reverting
  without data.
- Reading an enum from storage, calldata or memory whose tag names no variant
  reverts with `Panic(0x21)`. It used to reach an `INVALID` instruction, which
  consumes all remaining gas.
- Division and remainder by zero in unchecked code panic with `Panic(0x12)`,
  as they already did in checked code, instead of returning zero.

## Language improvements

`loop { .. }` repeats its body until a `break`, and a `loop` or `while true`
that never breaks is known to never complete, so a function can end in one
without a `core::panic()` after it. `Option<T>` compares with `==` when `T`
does:

```rust
use std::abi::DynString

fn first_digit(_ text: DynString) -> Option<u8> {
    for byte in text.span() {
        if byte >= b'0' && byte <= b'9' {
            return Option::Some(byte - b'0')
        }
    }
    Option::None
}

fn collatz_steps(_ start: u256) -> u256 {
    var n = start
    var steps = 0
    loop {
        if n == 1 {
            return steps
        }
        n = if n % 2 == 0 { n / 2 } else { 3 * n + 1 }
        steps += 1
    }
}

#[test]
fn language() {
    assert!(first_digit("fe 26.6") == Option::Some(2))
    assert!(first_digit("no digits") == Option::None)
    assert!(collatz_steps(27) == 111)
}
```

A few more:

- A trait effect now provides its supertraits, and theirs in turn: in a
  function that `uses (x: mut Super)`, a call that needs one of `Super`'s
  supertraits finds it.
- `is_some`, `unwrap` and friends work on the optional accesses that
  projections return, so `v.last().unwrap() = x` writes the last element.
- An integer literal that does not fit its type, such as `let x: u8 = 300`,
  is now rejected. It used to be silently truncated.
- `&=` and `^=` now work on `bool`.
- Unchecked arithmetic now applies to `Wei`, `Duration` and `Timestamp`, and
  to any type that implements the wrapping operator traits.

## Experimental WebAssembly backend

Fe can now compile to WebAssembly. With the `wasm` Cargo feature,
`fe build --backend wasm` produces a module with a 32-bit `usize` and a
manifest of its imports and exports, and `fe test --backend wasm` runs each
test as its own module under Node.js. Every non-generic `pub fn` at the root
of the file is exported, and `extern` functions become imports. `std::wasm`
provides the host effects `Log`, `Clock`, `Abort` and a read-only `Files`,
along with pure Fe mocks of each for testing.

The WebAssembly backend is not part of the release binaries yet; build the
compiler from source with `--features wasm,cranelift` to try it.

## Tooling

- `fe build` now warns when a contract's runtime code or initcode exceeds the
  EIP-170 or EIP-3860 deployment limits, and `fe build --emit sizes` writes
  the code size of each function, largest first.
- Contracts with the same name in different modules of one ingot can now be
  built and tested. Their artifacts are named by module path.
- Errors in patterns are reported much more reliably. Patterns that name an
  unresolved variant, a non-integer constant, or a constant that shadows a
  `recv` arm field used to be accepted and match anything, and are now
  rejected.
- `fe check` now reports type errors in `core` and `std` functions that the
  code being compiled reaches, instead of an internal error.

## Performance

- On native targets, the 64-bit `usize` makes index-heavy code up to 45 times
  faster, `leading_zeros` compiles to a single instruction, and fewer values
  are copied when passed to view parameters.
- `core::text::base64` encoding on the EVM costs about 65 gas per input byte
  instead of 284.
- A local array read at a computed index, such as `block[i]` in a loop, is
  stored in memory once instead of being copied for each read.
- `MemBuffer` appends are faster, and `MemBuffer` and `MemVec` no longer
  over-allocate on large appends.
- Compiling programs with large cycles of mutually recursive functions, such
  as an interpreter whose opcode handlers call each other, is much faster:
  one such program now builds in 20 s and 4.7 GB instead of 55 s and 13.3 GB.

<!-- Editorial note: the interpreter above is fevm (named in the release
notes). Name and link it here if it is public. -->

## Other fixes

- At `-O1` and `-O2`, a checked operation whose result was unused could check
  the wrong operand, so `b - (a & 255)` reverted with an overflow for
  `a = 2000` and `b = 1000`.
- A `mut` pattern binding of a packed storage field on a projection's result
  now writes to the field. The writes were silently lost.
- Calling through a mutable storage `Address`, such as `target.call(..)` on a
  `mut target: Address` field, is no longer rejected with an access conflict.
- A `let ... else` whose `else` block contains a nested scope keeps the
  pattern's bindings.
- Several internal errors in the access checker are fixed, among them `?` in
  generic methods that return `Option<mut T>`, `if let` with `|` patterns,
  and destructuring `recv` arm fields.

## Upgrading from 26.5

The most common changes existing code needs:

- Storage layouts changed: contract fields, packed value types in structs and
  map entries, and `StoragePackedArray` move to new slots and offsets. Data
  stored by a contract compiled with 26.5 must be migrated.
- `DynString`, `Bytes` and `DynArray` are no longer `Copy`. Use `clone()` or
  pass them as view parameters. `payload_span` is renamed to `span`, and
  `DynString::as_bytes` is replaced by `into_bytes`.
- `std::native::ByteBuffer` and `FixedStack` are removed in favor of
  `MemBuffer` and `MemVec`. `MemBuffer::alloc` is renamed `MemBuffer::new`.
- `std::io`'s character I/O (`HostIo`, `read_char`, `write_char`, ...) is
  replaced by the `Stdout`, `Stderr` and `Stdin` effects. A native `main` no
  longer takes `argc` and `argv`; use `uses (args: Args)` instead.
- `as` casts must be lossless on every target; use `downcast()` and friends
  for narrowing `usize` conversions.
- Calls to `extern` functions need an `unsafe` block.
- In `#[arithmetic(unchecked)]` code, operators on type parameters need the
  matching wrapping trait bound, such as `T: WrappingAdd`, and the wrapping
  traits take their operands `own`.
- `v[i] = x` now destroys the element it overwrites, so fill uninitialized
  memory from `MemArray::new_uninit` through raw places.
- Only the root module's `pub fn main()` without parameters is a program
  entry.

The [release notes](https://github.com/argotorg/fe/releases/tag/v26.6.0) list
every removal.

## Try it!

[Fe 26.6.0](https://github.com/argotorg/fe/releases/tag/v26.6.0) is available
now for Linux, macOS, and Windows. Let us know what you think!

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation
