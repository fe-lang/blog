
+++
title = "Fe Development Update #7"
date = "2021-08-04"
+++


It's been a couple months since our [last update](/posts/fe-development-update-6/). In this time, we've merged a total of [40 pull requests from 8 different contributors](https://github.com/ethereum/fe/pulls?q=is%3Apr+is%3Amerged+closed%3A2021-08-03%3E2021-05-29+). Here are some highlights.

## We shipped three more releases

- [v0.6.0-alpha](https://github.com/ethereum/fe/releases/tag/v0.6.0-alpha) and [v0.6.1-alpha](https://github.com/ethereum/fe/releases/tag/v0.6.1-alpha)
- [v0.7.0-alpha](https://github.com/ethereum/fe/releases/tag/v0.7.0-alpha)

## Improved error handling

**Support for custom errors:**

We added support for `revert <expression>` statements, where `<expression>` must be a struct type. The revert data is encoded as specified in [EIP-838](https://github.com/ethereum/EIPs/issues/838).

Example:

```rust
struct MyError:
    msg: u256
    val: bool
    
pub def revert_custom_error():
    revert MyError(msg=100, val=true)
```

Added in [#464](https://github.com/ethereum/fe/pull/464).

**Added builtin panic codes:**

Runtime checks now revert with the same panic codes used in Solidity. These codes can be found [here](https://docs.soliditylang.org/en/v0.8.4/control-structures.html?#panic-via-assert-and-error-via-require).

Added in [#476](https://github.com/ethereum/fe/pull/476).

**Better diagnostic messages:**

Errors found during static analysis are now printed using [codespan](https://github.com/brendanzab/codespan). This makes it easier to understand and fix invalid code.

Example:

```
error: value must be copied to memory
  ┌─ foo.fe:5:14
  │
5 │     self.baz(self.my_array)
  │              ^^^^^^^^^^^^^ this value is in storage
  │
  = Hint: values located in storage can be copied to memory using the `to_mem` function.
  = Example: `self.my_array.to_mem()`

```

Added in [#398](https://github.com/ethereum/fe/pull/398).

## ABI data checks

ABI encoded data is now checked to be well-formed before decoding. If the data being decoded is found to be ill-formed, the transaction will revert.

Added in [#440](https://github.com/ethereum/fe/pull/440). See the PR discussion for more info.

## Other features and bugfixes

-  Make duplicate function definitons a fatal error [#455](https://github.com/ethereum/fe/pull/455) 
-  Fix ICE when accessing an invalid attribute on a type [#445](https://github.com/ethereum/fe/pull/445)
-  `__init__` must be pub [#435](https://github.com/ethereum/fe/pull/435)
-  Add support for pragma statement [#426](https://github.com/ethereum/fe/pull/426)
-  Add tutorial that deploys and uses Guestbook on Görli [#420](https://github.com/ethereum/fe/pull/420) 
-  Make --optimize the default [#449](https://github.com/ethereum/fe/pull/449)
-  Capitalize Map type name [#431](https://github.com/ethereum/fe/pull/431)
-  Implement tuple destructuring [#428](https://github.com/ethereum/fe/pull/428)
-  Basic type inference of int literals and empty arrays [#429](https://github.com/ethereum/fe/pull/429)
-   Move tuple and list expr collection to lowering pass; support lowering of nested tuples [#459](https://github.com/ethereum/fe/pull/459)
-  Fix ICE #469 [#484](https://github.com/ethereum/fe/pull/484)
-  Fix ICE #450 [#462](https://github.com/ethereum/fe/pull/462)

## What's next

Our goal of shipping a non-alpha release this year still stands. Over the next few months, we will continue hardening the compiler, improving documentation, and polishing off existing features.

---

Stay tuned for more monthly updates and releases.
