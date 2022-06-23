+++
title = "Fe Development Update #5"
date = "2021-04-29"
+++


We've been hard at work since our [last update](/posts/fe-development-update-4/) and can't wait to talk about all the latest progress we've made. Let's dive right in.


## Team growth

Not only did we receive a steady flow of external contributions, we've also grown the core Fe team by two new (part-time) software engineers. Say hello to Sean and Satyam who will be helping us on our way to change the EVM language space. Fe is happy to have you 🙏

Part of their efforts have already formed the latest release that just shipped.

## We shipped v0.4.0-alpha "Diamond"

We've actually shipped two releases since the last update but many of the changes from the [0.3.0-alpha](https://github.com/ethereum/fe/releases/tag/v0.3.0-alpha) release were already covered in our [last development update](/posts/fe-development-update-4/). As usual, the entire list of changes can be found in the changelog on the [release page](https://github.com/ethereum/fe/releases/tag/v0.4.0-alpha). In this article, we'll focus on the two most exciting recent developments. 


## A brand new parser

Not only does the 0.4.0-alpha release come with a shiny name, it comes with a new, shiny parser, too.

Our old parser was by far the oldest part of the code base and it had served us well up to this point. Shout out to [David](https://github.com/davesque) who wrote it when he originally started the project under a different name.

As we are moving closer to our first non alpha release we've made it a high priority for Fe to have high quality, context-aware error messages. While this may not have been impossible with the old parser, the new handwritten recursive descent parser gives us all the flexibility and clarity that we need to enable great rust style error messages.

To give an example, consider this wrongly formatted source code:

```
contract Example:
val:u8
```

While we can and will tune the quality of our error messages, the following example of an actual Fe error message does already demonstrate the improved user experience that we got out of the parser rewrite so far.

![](https://storage.googleapis.com/ethereum-hackmd/upload_3c6767184497bd08fddde6d084ad6081.png)


We currently continue to streamline our error reporting across the different processing stages to take advantage of the improvements on all levels.

While the parser rewrite was mostly motivated by improving our error messages it will also help us to implement new features faster.


## Lowering pass

The other major improvement that just landed in the latest release is an entirely new compile phase called the "lowering pass". Lowering is compiler speak for what is commonly referred to as "desugaring".

In other words, whenever we say that something is just "syntactic sugar" for a longer, less-elegant syntax, it is the lowering pass's job to take that code and turn it into the less-elegant, but simpler syntax. This is a technique that many modern compilers use, including rustc.

By using lowering, we are able to simplify the implementation of new features and reduce compiler complexity.

### Tuples

To give a concrete example, our latest release comes with support for tuples, which can be used like this:

```
contract Foo:
    pub def bar(my_num: u256, my_bool: bool) -> (u256, bool):
        return (my_num, my_bool)
```

Fe's new lowering pass rewrites this as follows:

```
struct tuple_u256_bool:
    item0: u256
    item1: bool

contract Foo:
    pub def bar(my_num: u256, my_bool: bool) -> tuple_u256_bool:
        return tuple_u256_bool(item0=my_num, item1=my_bool)
```

As you can see, Tuples don't actually exist past the lowering stage, as Tuples in Fe are just syntactic sugar over structs (which by the way, is also true for Rust).

We also use the lowering pass for augmented assignments (e.g. `x += 1`) and plan to use it for many of the upcoming features. It's a real game changer, as it helps us to avoid code duplication and reduces the overall maintenance cost for the features we develop.


## Other features and bugfixes

- Support for revert messages in assert statements ([#288](https://github.com/ethereum/fe/issues/288))
- Support for augmented assignments ([#338](https://github.com/ethereum/fe/issues/338))
- Reject invalid emit ([#211](https://github.com/ethereum/fe/issues/211))
- Properly tokenize numeric literals when they start with 0 ([#331](https://github.com/ethereum/fe/issues/331))
- Reject non-string assert reasons as type error ([#335](https://github.com/ethereum/fe/issues/335))
- Reject code that creates a circular dependency when using `create` or `create2` ([#362](https://github.com/ethereum/fe/issues/362))


## What's next

Our plan is to ship our first non-alpha release in 2021 and hence our focus is currently on implementing the essential features that are still missing as well as eleminating bugs and improving the robustness of the compiler which includes building out tooling for *differential contract fuzzing*.

We will soon write a dedicated blog post that will shed more light on our plans for Fe's road to production.


---

Stay tuned for more monthly updates and releases.