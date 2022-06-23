+++
title = "Fe Development Update #2"
date = "2020-12-21"
+++

It's been a month since our [last development update](/posts/fe-development-update-1/) and we'd like to take some time once again to fill you in on our progress.

In this time, we've merged a total of 20 Pull Requests from 3 different people, finished implementing all the features required for an ERC-20 contract, expanded type support, and have begun planning our first release.

## ERC-20 support

Earlier in October, we set the year-end [goal](https://github.com/ethereum/fe/milestone/1?closed=1) of completing support for all of the features used in a basic [ERC-20 contract](https://github.com/ethereum/fe/blob/3826aea3a58bce2771d92ed7f197b170e7419aeb/compiler/tests/fixtures/erc20_token.fe). We're proud to say that we hit our target about a month earlier than planned. The compiled bytecode is fully tested using [rust-evm](https://github.com/rust-blockchain/evm) and appears to work just fine. Keep in mind, though, that the compiler is still experimental, so we do not recommend deploying any tokens to mainnet quite yet.

## Misc new features

- Support for all sizes of signed and unsigned integer types.
- Indexed event parameters.
- All types may be used as contract fields now. Previously, we only supported maps.
- The CLI can now emit pretty-printed Yul and JSON ABIs.
- Support for ternary statements (thanks [@satyamakgec](https://github.com/satyamakgec)).

## Release plan

We're looking forward to getting the compiler into people's hands and receiving feedback. Starting mid-January, we'll be cutting binary releases on our Github page every month. With these binaries, you will be able to generate contract ABIs, bytecode, and Yul IR. If you would like Fe and its tooling to accommodate you, please consider downloading a compatible binary and create issues for anything that seems out of place.

## What's next

Now that we've finished support for an ERC-20 contract, we will be turning our focus to a working implementation of the Uniswap V2 protocol. We plan on having this done by April of next year. By focusing on such a widely used platform, we are able to identify desirable features.

### Special thanks

Our project currently has ~80 contract fixtures that are deployed and tested using [rust-evm](https://github.com/rust-blockchain/evm). Being able to reliably test all of these contracts within a fraction of a second has been invaluable to the development process. We'd like to thank [@sorpass](https://github.com/sorpaas) and other contributors very much for the work they have done on this EVM implementation.