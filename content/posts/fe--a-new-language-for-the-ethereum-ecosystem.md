
+++
title = "Fe: a new language for the Ethereum ecosystem"
date = "2020-10-14"
+++

The majority of applications deployed on the Ethereum network these days are written in Solidity. We believe the Solidity team is doing a great job and are clearly doing a lot of things right to maintain their current market share. However, we also believe that more choices for developers will be a net positive for the ecosystem.

## Introducing Fe

We are excited to announce a new smart contract language for the Ethereum ecosystem named Fe (pronounced "fee"). The language was originally [born as a rewrite of the Vyper compiler (in Rust)](https://blog.ethereum.org/2020/01/08/update-on-the-vyper-compiler/) to address issues that were highlighted in the [Vyper Security Review](https://diligence.consensys.net/audits/2019/10/vyper/) by Consensys from another angle.

While the initial goal was to have an alternative Vyper compiler, eventually the languages started to diverge in their syntax and it was decided to make a clean cut with a new name. Fe was born.

"Fe" are the letters for the chemical element iron of the periodic table. Iron conveys a sense of durability, and this reinforces the notion of compiler correctness. Rust forms on iron, which ties the name back to the Rust language that the Fe compiler is written in.

### Goals

This project inherits a number of things from Vyper; namely it has a Pythonic syntax and emphasizes language safety. As such, the syntax of Fe is largely inspired by Python. This allows for readable and expressive code that would be familiar to developers who have used Python. Fe also uses static typing and limits dynamic behavior to reduce footguns and improve safety.

At this early stage in development the differences between Fe and Vyper are still limited. For now, one will notice that Fe borrows a few syntactic properties from Rust. It's likely that Fe will begin to more closely resemble Rust as we continue to add new features.

### Correctness of Fe's Implementation

Beyond the language itself, we are taking steps to ensure that the compiler implementation is correct. In other words, there should be a high degree of confidence that executable code produced by the Fe compiler will behave correctly with respect to the language specification.

Some of the steps we're taking to ensure correctness are listed below:

**Writing a language specification**

A compiler can not be demonstrated to be correct if there is no specification to check against. For this reason, we have begun writing a [specification](https://github.com/ethereum/fe/blob/master/spec/index.md) for the language, which borrows heavily from the [Rust reference](https://doc.rust-lang.org/stable/reference/) 🦀❤️. This specification will be written as we implement features. By the time we are ready for an audit, we will be able to produce a comprehensive specification.

**Implementing in Rust**

Rust is a systems language with strong safety guarantees. These safety guarantees prevent Rust programs from entering undefined behavior. For example, *null* pointers are not possible in safe Rust. This makes it so that Rust compiler catches bugs during compile time that would otherwise be encountered during runtime.

**Using distinct components**

Fe aims to separate components of the compiler into distinct libraries that follow standard compiler design guidelines. That is, we have implemented parsing, semantic-analysis, and compilation as separate libraries with their own APIs and tests. This separation of concerns makes it easier to understand the behavior of the compiler.

### Targeting Yul

The compiler targets [Yul](https://solidity.readthedocs.io/en/latest/yul.html) as an intermediate representation. Yul is a project being developed by the Solidity team and is intended to be a common denominator between multiple low level platforms, meaning that we do not need to write separate backends for EVM 1.0, EVM 1.5, and eWASM. Currently, the Solidity compiler provides experimental support for Yul -> EVM 1.0 compilation. For the time being, we are just using the Solidity backend for Yul compilation. This has saved us a significant amount of time.

Standardizing on YUL as an intermediate language may also prove as an convenient gateway to target Optimistic Rollup environments as recently highlighted by [Vitaliks Ethereum Roadmap post](https://ethereum-magicians.org/t/a-rollup-centric-ethereum-roadmap/4698).


### Progress

The [EBNF](https://en.wikipedia.org/wiki/Extended_Backus%E2%80%93Naur_form) grammar expected by the parser can be found [here](https://github.com/ethereum/fe/blob/master/parser/src/grammar/Fe.grammar). The parser provides support for everything specified in that grammar file and includes comprehensive testing.

Earlier this year, development started on the compiler pass. We were able to add support for a few simple contracts. Most notably, we were able to compile a simple [guestbook contract](https://github.com/ethereum/fe/blob/master/compiler/tests/fixtures/guest_book.fe) to functional bytecode.

In the past month, development on Fe has ramped up significantly. We are optimistic about adding support for all features used in an ERC20 contract and be able to compile one before the end of 2020. To be clear, the compiler will in no way be a suitable choice for a production ERC20 by that time, but we look forward to demonstrating the capabilities of Fe with such a well understood working example.

For the curious, here's a simple contract that is already fully functional today:

```
type BookMsg = bytes[100]

contract GuestBook:
    pub guest_book: map<address, BookMsg>

    event Signed:
        idx book_msg: BookMsg

    pub def sign(book_msg: BookMsg):
        self.guest_book[msg.sender] = book_msg

        emit Signed(book_msg=book_msg)

    pub def get_msg(addr: address) -> BookMsg:
        return self.guest_book[addr]
```

### Get in touch

We are committed to developing a language that will enrich the Ethereum developer community. If you are as excited about this effort as we are, don't hesitate to get in touch with us:

- [GitHub](https://github.com/ethereum/fe)
- [Gitter Chat](https://gitter.im/ethereum/fe)
- [Twitter](https://twitter.com/official_fe) 