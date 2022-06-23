
+++
title = "Fe Development Update #8"
date = "2021-10-05"
+++


It's been a couple months since our [last update](/posts/development-update-7/). In this time, we've merged a total of [20 pull requests from 7 different contributors](https://github.com/ethereum/fe/pulls?q=is%3Apr+is%3Amerged+closed%3A2021-10-04%3E2021-08-03). Here are some highlights.

## We shipped 2 more releases

- [v0.8.0-alpha "Haxonite"](https://github.com/ethereum/fe/releases/tag/v0.8.0-alpha)
- [v0.9.0-alpha "Iridium"](https://github.com/ethereum/fe/releases/tag/v0.9.0-alpha)

As always, you can find the binaries and notes on the release pages.

## `self` as a parameter

The `self` value is no longer implicitly defined in all code blocks. It must now be declared as the first parameter in a contract function signature.

This change was made as part of an effort to make function access more explicit. There is a similar change coming with [#558](https://github.com/ethereum/fe/issues/558).

Added in [#520](https://github.com/ethereum/fe/pull/520).

## `fn` instead of `def`

Fe no longer uses the `def` keyword as a label for function definitions. We use `fn` instead now. This makes the syntax more clear.

Added in [#496](https://github.com/ethereum/fe/pull/496).

## Query-based analysis

The analyzer was previously implemented as a single pass through the AST, which meant that it wasn't possible to refer to a type defined later in the file or define recursive types. To solve this problem and to improve the overall design of the analyzer, we now use [Salsa](https://crates.io/crates/salsa), and thus a query-based style.

Salsa is used extensively in [rust-analyzer](https://github.com/rust-analyzer/rust-analyzer), which is where we got the idea to use it.

Added in [#468](https://github.com/ethereum/fe/pull/468).

## Other features and bugfixes

- Typo fix in docs (thanks [@jacobkaufmann](https://github.com/jacobkaufmann)!) [#549](https://github.com/ethereum/fe/pull/549)
- Fuzzer crash fixed [#546](https://github.com/ethereum/fe/pull/546)
- Readme improvements (thanks [@zora89](https://github.com/zora89)!) [#544](https://github.com/ethereum/fe/pull/544)
- Pretty printed display of AST [#540](https://github.com/ethereum/fe/pull/540)
- Analyzer checks for shadowing of built-ins and generic arg lists where they don't belong [#539](https://github.com/ethereum/fe/pull/539)
- Don't ignore non-fatal parser errors when analysis succeeds [#535](https://github.com/ethereum/fe/pull/535)
- Fix "analysis failed but no diagnostics were emitted" panics [#534](https://github.com/ethereum/fe/pull/534)
- Add support for numeric invert operator [#526](https://github.com/ethereum/fe/pull/526)
- Check labels in function calls on self and external contracts [#518](https://github.com/ethereum/fe/pull/518)
- Cover all remaining statements and expressions in the spec [#514](https://github.com/ethereum/fe/pull/514)
- Fuzzer crash fixed (thanks [@andy-ow](https://github.com/andy-ow)!) [#510](https://github.com/ethereum/fe/pull/510)
- `let` var decl (thanks [@WilfredTA](https://github.com/WilfredTA)!) [#509](https://github.com/ethereum/fe/pull/509)
- Validate string literals to only allow a subset of ASCII chars [#506](https://github.com/ethereum/fe/pull/506)
- Reject certain code that should return but doesn't  [#502](https://github.com/ethereum/fe/pull/502)
- Overhaul spec content [#489](https://github.com/ethereum/fe/pull/489)

## What's next

We are still focused on [cutting a beta release](/posts/fes-path-to-production/) before the end of the year and will keep the community updated. For more information about our immediate goals and to see whats under development, please see the issues and PRs in our [repository](https://github.com/ethereum/fe).

---

Stay tuned for more updates and monthly releases.
