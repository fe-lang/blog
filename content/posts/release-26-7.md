+++
title = "Fe 26.7.0"
date = "2026-11-18"
+++

<!-- Editorial note: release-day copy, based on the v26.7.0 tag
(e6e6342b252082f3fd8af5b9f763cb13296bf0a1, 2026-11-18), compared with v26.6.0.
All Fe examples were checked with a `--profile dist --features
fe/cranelift,fe/wasm` build of that commit; the native examples were built and
run on x86-64 Linux, the WebAssembly example in Node.js 24. The "Performance"
numbers are taken from the release notes, except the `base ** 2` gas figures,
which come from PR #2028. Confirm the platform artifacts and
remove draft status before publishing. -->

The Fe team is happy to announce the release of Fe 26.7.0!

26.6 taught native Fe programs to print, read files and run other programs.
26.7 lets them talk to the network: `std::net` brings TCP, UDP, a poller and
DNS lookups, and files and sockets now read and write through common `Read`
and `Write` traits, with a `BufReader` on top. The WebAssembly backend now ships in
the release binaries and builds whole ingots, native programs run on
AArch64 Linux, and calls can leave out generic arguments the compiler can
infer. On the EVM, much of the standard library got cheaper, from text
processing to base64, and a new `Call::forward_delegatecall` makes proxies
simple.

The effect system is stricter in this release, which can reject code that
26.6 accepted; the [upgrade notes](#upgrading-from-26-6) at the end summarize
what existing code needs. Highlights are below; the full changelog is here:
[v26.7.0](https://github.com/argotorg/fe/releases/tag/v26.7.0)

## Networking

`std::net` adds networking for native programs on Linux and macOS. Like the
file system and processes in 26.6, the network is a capability: a function
needs `Net` in its `uses` clause to open a socket. Here is a small TCP server
that sends every line it receives back to the client:

```rust
use core::MemBuffer
use std::io::{BufReader, Error, Stdout, Write}
use std::net::{Net, SocketAddr}

pub fn main() -> i32 uses (out: mut Stdout, net: mut Net) {
    match serve() {
        Result::Ok(()) => 0,
        Result::Err(error) => {
            println!("echo: ", error)
            1
        }
    }
}

fn serve() -> Result<Error, ()> uses (out: mut Stdout, net: mut Net) {
    var listener = net.listen(SocketAddr::parse("127.0.0.1:7878").unwrap())?
    println!("listening on ", listener.local_addr()?)
    loop {
        let (stream, peer) = listener.accept()?
        println!("connection from ", peer)
        var conn = BufReader::new(stream)
        var line = MemBuffer::empty()
        while conn.read_line(mut line)? {
            conn.inner().write_all(format!("echo: ", line, "\n").span())?
            line.clear()
        }
    }
}
```

```sh
fe build --backend native --out-dir out echo.fe
./out/echo &
printf 'hello\nfe\n' | nc 127.0.0.1 7878   # prints "echo: hello" and "echo: fe"
```

Only making a socket needs `Net`: once a function owns a `TcpStream`, it can
read and write it without the capability. Beyond the example:

- `Net::connect` and `connect_timeout` open a `TcpStream`, `listen` a
  `TcpListener`, and `bind_udp` a `UdpSocket`. Sockets have read and write
  timeouts, non-blocking modes and `shutdown`, and close when dropped.
- `Net::lookup` resolves a host name to its addresses.
- `Poller` waits for events on many sockets at once, with `epoll` on Linux and
  `kqueue` on macOS, for servers that handle many connections in one thread.
- `Ipv4Addr`, `Ipv6Addr`, `IpAddr` and `SocketAddr` parse and print addresses
  on every target, the EVM included.

## Streams and files

The echo server reads its socket through `BufReader`. That works because
`std::io` now has `Read` and `Write` traits, which sockets, files and the new
`MemReader` implement. `BufReader` wraps any `Read` and reads a byte or a line
at a time, and `read_line_max` limits how long a line may get, which a server
reading from untrusted peers needs.

`std::fs` gains `File`: `Fs::open`, `create` and `open_with` open one, and it
is closed when dropped. So a small `grep` now reads its file a line at a time
instead of loading it whole:

```rust
use core::MemBuffer
use std::env::Args
use std::fs::Fs
use std::io::{BufReader, Error, Stdout}

pub fn main() -> i32 uses (out: mut Stdout, args: Args, fs: Fs) {
    match grep() {
        Result::Ok(matches) => if matches > 0 { 0 } else { 1 },
        Result::Err(error) => {
            println!("grep: ", error)
            2
        }
    }
}

fn grep() -> Result<Error, usize> uses (out: mut Stdout, args: Args, fs: Fs) {
    var reader = BufReader::new(fs.open(args.get(2))?)
    var line = MemBuffer::empty()
    var number: usize = 0
    var matches: usize = 0
    while reader.read_line(mut line)? {
        number += 1
        if line.span().index_of(args.get(1)).is_some() {
            println!(number, ": ", line)
            matches += 1
        }
        line.clear()
    }
    Result::Ok(matches)
}
```

`OpenOptions` covers the other cases, such as appending or creating a file
only if it doesn't exist. `io::Error` has new kinds for sockets, such as
`WouldBlock`, `TimedOut` and `ConnectionRefused`, and `Error::new(kind)` makes
an error without a host error number.

## WebAssembly

The WebAssembly backend introduced in 26.6 is now part of the release
binaries, so `fe build --backend wasm` and `fe test --backend wasm` work
without building the compiler from source. It has also grown a lot:

- `fe build --backend wasm` builds ingots and workspaces, not just single
  files. As in native libraries, a module exports the functions marked
  `#[unsafe(export)]`, wherever they are in the ingot, and they may call the
  rest of the ingot and its dependencies.
- `std::wasm::Host` provides `Stdout`, `Stderr` and `Stdin`, so code that
  prints with `println!` builds for WebAssembly as well as for native
  targets.
- A panic passes Solidity-style revert data, such as `Panic(0x11)` for an
  overflow, to the host instead of trapping, and `fe test --backend wasm`
  shows a failed test's output and revert data, as the other backends do.
- Modules are at least a third smaller, 128- and 256-bit division is 20 to 40
  times faster, dense `match`es compile to jump tables, and self-recursive
  tail calls no longer grow the stack.

The `fe_gcd` function from the 26.6 announcement builds into a WebAssembly
module unchanged:

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

```sh
fe build --backend wasm --out-dir out gcd.fe   # writes gcd.wasm and gcd.manifest.json
```

```js
import { readFile } from "node:fs/promises";

// `x % y` can panic, so the module imports the revert hook of the host contract.
const env = { __fe_revert: () => { throw new Error("fe_gcd reverted"); } };
const { instance } = await WebAssembly.instantiate(await readFile("out/gcd.wasm"), { env });
console.log(instance.exports.fe_gcd(1071n, 462n)); // 21n
```

The manifest lists the module's imports and exports. A module that uses host
effects, such as `Stdout` or files, imports them too;
[`examples/wasm/host.mjs`](https://github.com/argotorg/fe/blob/master/examples/wasm/host.mjs)
is a host for Node.js that provides them.

## AArch64 Linux

Native executables and `fe test --backend native` now work on AArch64 Linux,
as well as on x86-64 Linux and AArch64 macOS. `#[cfg(target_arch =
"x86_64")]` and `#[cfg(target_arch = "aarch64")]` select items by the
architecture that native code runs on, as `target_os` does by the operating
system.

## Language improvements

### Partial generic arguments

A call can now give only some of its callee's generic arguments. They fill the
parameters from the left, and the rest are inferred or take their defaults.
`_` stands for an argument to infer, so later arguments can be given while
earlier ones are inferred:

```rust
fn repeat<const N: usize, T: Copy>(_ value: T) -> [T; N] {
    [value; N]
}

fn pick<T: Copy, const I: usize>(_ items: [T; 4]) -> T {
    items[I]
}

#[test]
fn partial_generic_arguments() {
    let seven: u8 = 7
    let bytes = repeat<4>(seven)
    assert!(bytes[3] == 7)

    let words: [u256; 4] = [10, 20, 30, 40]
    assert!(pick<_, 2>(words) == 30)
}
```

A call that leaves a generic parameter uninferred now names it, and suggests
the arguments that would give it, as in "consider giving it explicitly:
`op<1, F>`".

### `#[cold]` functions

`#[cold]` marks a function as rarely called, such as one that reports a
fault. The optimizer doesn't inline it into callers that aren't cold, and
native code moves the paths that call it out of the way of the rest of their
function:

```rust
enum Status {
    Charged { left: u64 },
    OutOfGas { pc: usize },
}

#[cold]
fn out_of_gas(pc: usize) -> Status {
    Status::OutOfGas { pc }
}

fn charge(gas: u64, cost: u64, pc: usize) -> Status {
    if cost > gas {
        return out_of_gas(pc)
    }
    Status::Charged { left: gas - cost }
}
```

See the
[inline and cold guide](https://github.com/argotorg/fe/blob/master/docs/language/inline-and-cold.md)
for how it combines with `#[inline]`.

### Variadic `extern` functions

A trailing `...` makes an `extern` function variadic, so native programs can
call C functions such as `fcntl`:

```rust
extern {
    fn fcntl(_ fd: i32, _ cmd: i32, ...) -> i32
}
```

The extra arguments must be 32- or 64-bit integers or raw pointers, and
variadic functions are native-only.

### Stricter effects

A call's effects now follow the rule its arguments do: two effects of one call
may not overlap where one of them is `mut`. In return, a function can rely on
its effects being disjoint, so it may iterate one effect while it writes
another. A provider is also no longer chosen by matching its name to the
callee's effect label: when a scope has two providers of one key,
`with (Key = value)` picks one. The
[effects guide](https://github.com/argotorg/fe/blob/master/docs/language/effects.md)
has the full rules. Along the way, several bugs where writes through `mut`
effects to packed storage fields were lost are fixed.

## Proxies with `forward_delegatecall`

`Call::forward_delegatecall(addr, gas)` forwards the current calldata to
`addr` with `DELEGATECALL`, and returns or reverts with the callee's
returndata unchanged. That is the whole fallback of a delegating proxy:

```rust
use std::evm::{Address, Call, Ctx}

pub contract Proxy uses (ctx: Ctx, call: mut Call) {
    implementation: Address,

    init(target: Address) uses (mut implementation) {
        implementation = target
    }

    recv {
        #[payable]
        _ uses (ctx, implementation, mut call) {
            call.forward_delegatecall(addr: implementation, gas: ctx.gas())
        }
    }
}
```

It spends about 100 to 170 gas a call less than a proxy that copies through
`MemBuffer`, `raw_delegatecall` and `copy_returndata`.

## Performance

- Much of the standard library uses less gas on the EVM. Text searching,
  splitting, comparing and ordering work a word at a time instead of a byte at
  a time, base64 decoding of long inputs uses about 90% less gas, and base58,
  hex and decimal formatting, number parsing, RLP, `isqrt`, `mul_div` and
  fixed-point rescaling are all cheaper.
- Typed calls whose returned data has a static ABI size decode it straight
  from the call output, and copying `Bytes` and `DynString` payloads clears
  only the final padding word.
- `x ** 2` and other checked powers with a small constant exponent compile to
  at most two checked multiplications: `base ** 2` costs 508 gas instead of
  692.
- Contracts with immutable fields no longer carry constant data their code
  never reads, which shrinks contracts in the Liquity and Uniswap v4 ports by
  up to 1,236 bytes, and constants that hold a single value are passed like
  computed values instead of being read from the contract code.
- `fe test` on the EVM compiles the selected tests into one contract and
  deploys it once: 20 tests calling a 300-function library went from 24 s to
  1.1 s of CPU time.
- Native `MemVec` and `MemBuffer` grow with `realloc`, which extends or remaps
  an allocation instead of copying it.

## Other fixes

- Optimized native and WebAssembly code no longer moves a division ahead of
  the test that guards it, so `if d != 0 { s += x / d }` in a loop can't trap
  with `d == 0` anymore.
- Writes to packed storage fields through `mut` arguments, `mut` effects and
  projections are no longer lost, including when a callee ends the call
  successfully while the access is open.
- Invalid trait arguments in qualified paths and errors in a trait's
  associated type defaults are reported where they are written.
- The language server applies edits in the order they arrive, shows signature
  help for many more kinds of calls, and no longer panics on several unusual
  workspace layouts.

## Upgrading from 26.6

The most common changes existing code needs:

- Two effects of one call may no longer overlap where one is `mut`, such as
  `with (totals.log, mut totals) { settle() }`.
- Providers are no longer matched to effects by name. A `with` block or
  scope with two providers of one key needs `with (Key = value)` to choose,
  and a `uses` list may name each key only once.
- The `EffectRef` marker trait is removed. Every type implemented it, so
  bounds that name it can be dropped.
- A WebAssembly module now exports only the functions marked
  `#[unsafe(export)]`, not every `pub fn` at the root of the file. Hosts need
  to implement version 3 of the host contract, which adds `__fe_revert`,
  `abort` and `sys_wasm_files_read`, and make a new instance of a module
  after a failed call.
- `io::Error::code()` now returns an `Option<i32>`.
- A native program that replaces `malloc` and `free` must now replace
  `realloc` too.

The [release notes](https://github.com/argotorg/fe/releases/tag/v26.7.0) list
every change.

## Try it!

[Fe 26.7.0](https://github.com/argotorg/fe/releases/tag/v26.7.0) is available
now for Linux, macOS, and Windows. Let us know what you think!

The [Fe Builders Challenge](https://fe-lang.org/contest/) is still running
until November 24. Any Fe from 26.5.1 on counts, so you can switch to 26.7 or
stay where you are.

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation
