
+++
title = "Fe 26.0.0: A Fresh Start"
date = "2026-03-31"
+++

In November 2023, we released Fe v0.26.0. Then, things went quiet. We spent the time rebuilding the compiler from the ground up.

Today we are releasing **Fe 26.0.0**. This post covers why we rewrote the compiler, what changed, and where the project stands now.

## Why a rewrite?

When we wrote ["Beyond alpha"](/posts/beyond-alpha-preparing-fe-for-the-future) in March 2023, we outlined an ambitious list of features: full generics, traits, const functions, an LSP, and a native compiler backend. What we underestimated was the degree of 'architectural resistance' the old codebase would mount against these features.

The old compiler had been extended incrementally over the years and some of its core abstractions had reached their limits. Generics are a good example: the previous implementation supported generic *functions*, but generic structs and enums were not possible without fundamental changes to how the compiler represented types internally. Generics had been bolted on rather than designed in, and that pattern repeated across other parts of the system.

We chose to start over to build the foundations these features actually require. The result is a new compiler with a powerful type system, a new contract interaction model, and a modern developer experience. It is not an incremental update. It is a fresh start. This is also reflected in the version number and why we called it 26.0.0 instead of 0.27.0. New releases will follow the pattern of `<year>.<minor>.<patch>`, so this is the first release of 2026. The fresh start also extends to the project's home: Fe is no longer housed at the Ethereum Foundation and now lives at the [Argot Collective](https://argot.org), a research collective focused on language and tooling work for the Ethereum ecosystem.

## The language

Fe 26.0.0 is a new compiler, a new type system, and in many ways a new language, while staying true to Fe's original design principles: **safety, explicitness, and readability**.

### EVM-native message passing

The old contract interaction model has been replaced. Contracts now communicate through `msg` types and `recv` handlers, a design that directly mirrors the EVM's transaction-based execution model.

This is not just a syntactic change. The new model is structurally better and eliminates a class of issues that plagued the previous approach. One shortcoming of the old model was that contracts and structs very much looked alike on the surface, but had very different semantics. In the new model, contracts are intentionally very different from structs. For instance, they can not have functions apart from the special `init` constructor.

Another issue was how contracts would expose their public functions in a way that plays nicely with the existing Solidity ABI. Let's serve Uniswap's `function exactInputSingle(.., uint24 fee,..)` as an example. Not only does idiomatic Fe code use snake case (e.g. `exact_input_single`), but Solidity's ABI also uses types that we do not want to support as built-in types in Fe (e.g. `uint24`). The new message-passing model is flexible enough to support different ABIs and the Fe standard library includes a module to support the Solidity ABI without making it a core part of the language.

### Explicit by default

Fe's novel effect system makes side effects visible. Every function declares its capabilities through a `uses` clause: storage access, event emission, external calls, contract creation. If a function doesn't declare it, it can't do it. The compiler enforces this.

All bindings, storage fields, and effect parameters default to immutable. You must explicitly opt in to mutability with `mut`. The compiler rejects writes to immutable state.

The result is code where you can read a function signature and immediately understand what it can and cannot do.

### A real type system

This is where the rewrite pays off most directly. Fe now has:

- **Generics** across functions, structs, enums, and traits, with trait bounds
- **Traits** as shared interfaces, used throughout the standard library for `Encode`, `Decode`, `Default`, and more
- **Higher-Kinded Types** via `* -> *` bounds, enabling abstractions like `Functor` and `Monad`
- **Pattern matching** with exhaustiveness checking. The compiler verifies all cases are covered
- **Type inference** that reduces boilerplate without sacrificing clarity
- **Const functions** that are evaluated at compile time, enabling computations like hash selectors to be resolved during compilation rather than at runtime

The type system is expressive enough that **Fe's standard library is written entirely in Fe**. That wasn't possible before, and it is perhaps the clearest measure of how far the language has come.

## Sonatina: a new compiler backend

Fe 26.0.0 ships with a new default backend: **Sonatina**, a compiler backend built from the ground up by the Fe team.

Sonatina is based on [Static Single-Assignment form (SSA)](https://en.wikipedia.org/wiki/Static_single-assignment_form), a well-established compiler intermediate representation used by LLVM and other major compiler frameworks. This replaces the previous approach of compiling to Yul and relying on the Solidity compiler for the final compilation step.

The move to SSA opens the door to a range of optimizations that were simply not feasible when targeting Yul. While Sonatina is still maturing, it already serves as Fe's default backend and will be the foundation for all future optimization work. The Yul backend is still available for those who want it, but requires a separate `solc` installation.

## Batteries included

A language is only as good as the tools around it. Fe 26.0.0 ships with an integrated toolchain designed to provide a smooth developer experience from day one:

- **`fe build`**: Compile your project
- **`fe test`**: Run tests with built-in EVM simulation, no external tooling required
- **`fe fmt`**: An opinionated code formatter to keep codebases consistent
- **LSP support**: Editor integration for diagnostics, completions, and navigation
- **`fe doc`**: Generate documentation from your source code
- **Package manager**: Organize and share code through Fe's package system, with packages called *ingots*

On top of that, [Sourcify](https://sourcify.dev) already supports Fe, which means verified onchain contracts are available from day one. This is something the old Fe never had. A big thank you to the Sourcify team for making this happen.

The goal is a cohesive, well-integrated development experience, and we intend to keep raising the bar here.

## Where we stand

Let's be direct: **Fe 26.0.0 is not production-ready.**

This is a first release of a new compiler. It needs more testing, more polish, and a lot more real-world usage before anyone should trust it with serious value. The work ahead includes extensive test coverage, differential fuzzing against equivalent Solidity implementations, and the kind of battle-hardening that only comes with time and use.

That said, we are not releasing into a vacuum. We are already working closely with teams who are building on Fe, and real Fe contracts will be deployed to mainnet very soon. More on that in a separate announcement.

Fe 26.0.0 is the foundation. It is solid enough to build on, experiment with, and push things forward. But it would be irresponsible to pretend it's ready for the next Uniswap. We would rather be honest about where we are than oversell what we have.

## Language diversity matters

We believe the Ethereum ecosystem benefits from having multiple smart contract languages. Not because any single language is broken, but because diversity drives innovation and research into how we can write safer, more correct software.

Fe is our exploration of that belief: a language that makes every side effect visible, prevents classes of bugs before they happen, and pairs a modern developer experience with a strict safety model.

## Try it

Fe 26.0.0 is available now.

- **[fe-lang.org](https://fe-lang.org)**: The best starting point
- **[What is Fe?](https://fe-lang.org/getting-started/what-is-fe/)**: Learn about the language
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation

We'd love for you to try it, break it, and tell us what you think. This is the beginning.
