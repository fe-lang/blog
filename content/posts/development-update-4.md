+++
title = "Fe Development Update #4"
date = "2021-03-22"
+++

Hello, it's time for another Fe development update. There's alot to share since the [last one](https://snakecharmers.ethereum.org/fe-development-update-3/).

## We shipped v0.2.0-alpha "Borax"

This release contains many of the improvements mentioned in our last development update. You can find more details on the [release page](https://github.com/ethereum/fe/releases/tag/v0.2.0-alpha). 

## Uniswap Demo

In December of last year, we set a goal to support the features needed for a basic implementation of the Uniswap-V2 core contracts before April. The features were catalogued in this [Github Milestone](https://github.com/ethereum/fe/issues?q=is%3Aissue+milestone%3A%22Uniswap+Demo%22) and tagged with priority levels. We were able to close all high-priority issues and added a [test](https://github.com/ethereum/fe/blob/master/compiler/tests/demo_uniswap.rs) that demonstrates the behaviour of our implementation. In short, we are able to do the following:

- Deploy the Uniswap factory contract.
- Create a new pair using the factory contract.
- Add liquidity to the pair.
- Perform a swap.
- Withdraw liquidity.

There are still a few rough edges, though. These are documented in the [Uniswap module](https://github.com/ethereum/fe/blob/master/compiler/tests/fixtures/demos/uniswap.fe) using `TODO` comments that link to issues. The remaining issues will be worked on over the next few months, but are not of high priority.

## Safe arithmetic

One of Fe's core promises is to perform safe arithmetic operations by default. This is something that you'll find in our next release. Now if the result of an arithmetic operation, such as `x + y`, exceeds or falls below the upper or lower limit of the type, the transaction reverts. Developers have so far relied on the [SafeMath](https://docs.openzeppelin.com/contracts/2.x/api/math#SafeMath) library to perform these kind of safety checks. It's worth pointing out that Fe also checks *power* operations (i.e. `base ** exponent`), which the SafeMath library does not check. Fe's integrated arithmetic checks use the same Yul code as Solidity 0.8.0 (Thanks Solidity!).

In the future, we will likely add support for a special `wrapping` type [similar to Rust](https://doc.rust-lang.org/std/num/struct.Wrapping.html) that allows develops to *explicitly* opt-out from these checks. This is something that may be used to save gas, if you know what you're doing.

Related PRs: [#265](https://github.com/ethereum/fe/pull/265), [#267](https://github.com/ethereum/fe/pull/267), [#271](https://github.com/ethereum/fe/pull/271), [#312](https://github.com/ethereum/fe/pull/312), [#313](https://github.com/ethereum/fe/pull/313)

## More work on structs

[Last month](https://snakecharmers.ethereum.org/fe-development-update-3/) we shipped basic support for structs. Since then, we've landed some new improvements to our struct support.

- Accept structs as parameters to public functions or return them from public functions ([#296](https://github.com/ethereum/fe/pull/296))
- Update individual struct fields in storage ([#246](https://github.com/ethereum/fe/pull/246))
- Require keyword syntax to initialize structs ([#260](https://github.com/ethereum/fe/pull/260))


## Other features and bugfixes

- Prevent numeric literals from exceeding 256 bits ([#247](https://github.com/ethereum/fe/pull/247))
- Support boolean `not` operator ([#264](https://github.com/ethereum/fe/pull/264))
- Support boolean `and` operator ([#270](https://github.com/ethereum/fe/pull/270/))
- Support boolean `or` operator ([#270](https://github.com/ethereum/fe/pull/270/))
- Support`self.address` ([#270](https://github.com/ethereum/fe/pull/270/))
- Expose `abi_encode` function ([266](https://github.com/ethereum/fe/pull/266))
- Support`msg.sig` ([#311](https://github.com/ethereum/fe/pull/311))
- Fix several cases where conflicting names were not properly handled ([#317](https://github.com/ethereum/fe/pull/317))


## Continued compilation fuzzing

[agroce](https://github.com/agroce) has continued fuzzing the Fe compiler. Since our last development update, he has found [12 instances](https://github.com/ethereum/fe/issues?q=is%3Aissue+author%3Aagroce+created%3A%3E2021-02-10) where the compiler crashes for some input. These bugs often point to missing checks in the fe-analyzer library. Investigating them is very insightful. Thanks Alex! You can checkout the fuzzer [here](https://github.com/agroce/afl-compiler-fuzzer).

## What's next

Here are a few things we'll be working on over the next few months:

- **More checking**: Compilation fuzzing has shown us that we need to be checking source code more thoroughly. We'll focus on adding complete checking.
- **Lowering pass**: This makes the compiler more composable and transparent. It will first be used to support tuples.
- **Differential contract fuzzing**: We'll be making sure our demo contracts  work exactly like their Solidity counterparts.
- **Improved errors**: We'll make error messages more clear and useful.

You can also expect more demos, but they'll be smaller topics of discussion.

---

Stay tuned for more monthly updates and releases.