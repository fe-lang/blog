
+++
title = "Beyond alpha: Preparing Fe for the future"
date = "2023-03-31"
+++



Today we like to reflect on our progress and share our plans for the future of Fe. December 2022 Fe hit the Ethereum mainnet for the very first time with the [deployment of our bug bounty contest](/posts/bountiful-break-things-and-get-paid). Although it was hacked shortly after, no *serious* issues were revealed. The initial hack was just a sloppy fat-finger-copy-and-paste issue on our end but we invite you to read the inside story from the bounty hunter's perspective because it's such a great read.

<div style="display: flex; justify-content: center;">
<blockquote class="twitter-tweet"<p lang="en" dir="ltr">I cracked <a href="https://twitter.com/official_fe?ref_src=twsrc%5Etfw">@official_fe</a> &#39;s bountiful code challenge 💸<br><br>I was beyond impressed by the language and had a wonderful time poring over the code<br><br>Here&#39;s how it happened - including my thoughts on Fe 🧵</p>&mdash; plotchy (@plotchy) <a href="https://twitter.com/plotchy/status/1600894668304105474?ref_src=twsrc%5Etfw">December 8, 2022</a></blockquote> <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
</div>

If you've been following our [recent updates](/posts/bountiful-round-2), you will know that we quickly fixed the issue and restarted the contest and that the ongoing bug bounty contest did not reveal any critical bugs. In fact, the bounty is still up for grabs, go check it out if you're interested.

This certainly doesn't mean that Fe is bug-free, quite the contrary, we expect the compiler to still have bugs and we want to invite you to find and report them.

However, it does mean that we are confident enough to drop the `-alpha` marker from releases, starting with the upcoming `0.22.0` release. As we've [mentioned in the past](/posts/path-to-production), dropping the `-alpha` marker does not imply that the language is stable or feature-complete. It will still take a long way to go before we get anywhere close to that. As we continue to follow semantic versioning our `0.x` releases continue to be *unstable*.

## A bright future

In fact, we are currently in the process of rewriting large parts of the Fe compiler. This is necessary because the existing code base is not well suited for the features we want to add in the future. When the current rewrite is finished it will enable more advanced features such as:

- Enhanced support for generics (e.g. generic structs, generic traits, multiple trait bounds, etc.)
- Improved trait support (e.g. trait inheritance, trait specialization, etc.)
- Const functions (Functions that can run at *compile time* rather than at *runtime*)
- Type inference
- Flexible abstraction on ABI encoding/decoding
- Support for Language Server Protocol (LSP)

Additionally, we're working to replace Fe's Solidity backend. Fe currently uses YUL as its intermediate language and rely on the Solidity compiler to convert YUL to EVM bytecode. We're developing a native LLVM-inspired backend called [Sonatina](https://github.com/fe-lang/sonatina), which will replace this dependency, allowing for more aggressive optimizations and a streamlined Rust-only compilation process.

In conclusion, we're thrilled with the progress Fe has made and are confident that the upcoming improvements will further enhance the language. We invite you to join us in exploring and experimenting with Fe as it continues to mature. Your feedback and contributions are invaluable as we work together to build a robust, feature-rich programming language.

Thank you for your support, and stay tuned for more exciting developments!
