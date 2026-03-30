
+++
title = "Fe 26: A Fresh Start"
date = "2026-03-31"
+++

The last public release of Fe was in November 2023. Since then, we've been
rethinking the language, rewriting the compiler, and redefining our place within
the Ethereum language and tooling ecosystem. Today, we're "relaunching" with
the release of Fe 26.0.

Note: this release is not ready for production use!

## What is Fe?

At its core, Fe is a Rust-like, EVM-native language. It has algebraic data
types, generics, traits, and compile-time code execution.
We've added an explicit, simplified borrowing model, with no lifetime
annotations, but with control over mutability, ownership, and borrowing.

We've redesigned Fe's high-level abstractions to better fit the EVM execution
model. Contracts are written as an explicit dispatch table, but with high-level
syntax. Instead of contract "functions", we now have message types and message
receive blocks. Access to state, context, and EVM capabilities is explicitly
guarded by a new effect/capability system.

Our goal is to allow powerful control at all levels of abstraction. If you need
control over storage layout, single-byte selectors, and custom encode/decode
logic, you should be able to do it within the high-level contract syntax. If you
need to write a contract as low-level functions that operate close to the
machine without the `contract` syntax getting in your way, you can, while still
having the power of a modern Rust-like language with rich data types and
generics. When you really need raw EVM ops, those are available too.


## Why a rewrite?

The original Fe language and compiler grew organically. It started with Python
syntax, became Rust-like, added limited generics, etc. We bolted on new features as long
as we could, but we needed a new foundation for proper support of generics,
traits, type inference, and other language features.

We also felt that Fe wasn't offering a compelling alternative to the existing
popular EVM languages. Solidity semantics with Rust-like syntax isn't enough. We
decided to refocus the project to target use cases where richer abstraction and
more explicit safety controls could provide real benefit. This includes cases
that are currently handled with assembly blocks or code generators, which could
ideally be reworked to use safer abstractions and generics without sacrificing
efficiency, and large projects that manage complex state and
interactions, which could benefit from stronger access controls and clarity.
Simpler projects should still be clean and ergonomic, but Fe aims to really
shine when things get complex.

We chose to start again, with a new programming model, a more powerful type
system, and a new compilation pipeline. Accordingly, we've decided to abandon
the 0.X versioning scheme from 2023, in favor of `<year>.<minor>.<patch>`; 1.0
suggests stability that we don't yet have, and 26 happens to be Fe's atomic
number (which will be nice until next year). The fresh start also extends to
the project's home: Fe is no longer developed within the Ethereum Foundation; it
now lives at the [Argot Collective](https://argot.org), a research and
development collective focused on language and tooling work for the Ethereum ecosystem.


## Sonatina: a new compiler backend

The entire compiler stack is new, from the parser to EVM codegen. Fe 26.0 ships
with a new default backend: **Sonatina**. Sonatina is based on SSA (Static
Single-Assignment) control-flow-graph form, a representation used by many world-class compilers.
This allows us to benefit from a wealth of compiler optimization research and prior art.
Sonatina IR is relatively high-level, right type information is
propagated from Fe to Sonatina IR to unlock more aggressive optimizations.

Sonatina's EVM backend uses intelligent memory management and stack
spilling. There are no stack-too-deep errors, and there's no limitation on call graph
complexity. Non-recursive code will use efficient static memory locations for
statically-sized types (with re-use where possible to minimize memory expansion
costs), and recursive code uses dynamic call frames for memory allocations.

This replaces the previous approach of compiling to Yul and relying on the
Solidity compiler for the final compilation step. While Sonatina is still
maturing, it already serves as Fe's default backend and will be the foundation
for all future optimization work. The Yul backend is still available, but
requires a separate `solc` installation.


## Tooling

Fe 26.0 ships with an integrated toolchain, similar to the Rust tooling.
Fe projects are organized similarly to Rust projects, with
a root `fe.toml` config file; a project can be a single package or multiple
packages (called "ingots").

- **`fe check`** runs compiler checks and reports any issues.
- **`fe build`** compiles all contracts to EVM bytecode.
- **`fe test`** runs test functions annotated by `#[test]`.
- **`fe fmt`** applies (configurable) opinionated code formatting rules.
- **`fe doc`** generates documentation for your code from `///` doc comments.
- **LSP support**: `fe lsp` runs a language server for integration with editors, for diagnostics, completions, navigation, and formatting.
- **Package management**: your project can depend on external ingots in other local paths, or from a remote Git URL with a commit hash.

[Sourcify](https://sourcify.dev) already supports Fe, which means verified
on-chain contracts are available from day one. A big thank you to the Sourcify team
for making this happen.


## Where we stand

**Fe 26.0 is not production-ready.** This is the first release of a new
compiler. It has bugs, features are missing, the standard library is limited,
and it generates sub-par EVM bytecode in many cases. Testing support needs work, debugging
support is nonexistent. Integration with ecosystem tools like Foundry and Hardhat is
missing. In some places, the flexibility and power we plan to support isn't
fully unlocked.

We'll be releasing regular updates going forward. Short-term focus areas are:

- Compiler hardening via fuzzing, additional test cases, a suite of
  cross-language comparisons to ensure correct behavior and good performance.
- Improved EVM bytecode generation.
- First-class debugging support.
- Fully decoupling Solidity ABI assumptions to unlock customized selector and
  calldata encode/decode behavior within the high-level contract abstraction.
- A richer standard library, and external libraries.

There will likely be breaking changes in the near future. As the language and
compiler mature, we'll decide on and communicate stability guarantees.


## Language diversity

We believe the Ethereum ecosystem benefits from having multiple smart contract
languages. Fe doesn't aim to replace established languages like Solidity and
Vyper, or outcompete new languages like Plank or Ora, but to be a useful tool
for the projects and people it suits. We also hope to foster collaboration and
friendly competition, via projects like a community comparative benchmarking
suite, where we can collectively learn which compilers are optimizing which
patterns well, and we can share ideas for the benefit of the entire ecosystem.
We also aim to make Sonatina a useful backend option for other language projects.

## Try it!

Fe 26.0.0 is available now.

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation

We'd love for you to try it, break it, and tell us what you think. There's much
more to come.
