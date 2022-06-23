+++
title = "Fe Development Update #1"
date = "2020-11-20"
+++

It's been roughly a month since we officially [announced Fe](https://snakecharmers.ethereum.org/fe-a-new-language-for-the-ethereum-ecosystem/) as a new EVM compatible language. Since then, we've made vast progress and want to give the community a chance to catch up with the recent development.

There have been a total of 23 merged Pull Requests by 4 different people and we would like to take the chance to highlight some of the development.

## Say hello to our official logo

<img alt="Fe logo" src="https://raw.githubusercontent.com/ethereum/fe/master/logo/fe_svg/fe_source.svg" style="width: 200px; display: block; margin: auto;">
    
As all Fe development happens entirely in the open, we were fortunate to have designer [Daniel Iñiguez show up to offer his help](https://github.com/ethereum/fe/issues/38) and create this logo for Fe. It is "Fe" written in iron blocks.

## Constructors

Fe can now handle constructors with a syntax similar to that of Python. Here is an example:

```Python
contract Foo:
    bar: map<u256, u256>

    pub def __init__(baz: u256, bing: u256):
        self.bar[42] = baz + bing
```

## Implicit return of `()`

Fe now treats functions that do not explicitly return anything the same way that Rust does by implicitly returning `()` (an empty `Tuple`). To let code speak; all of these mean the same thing:

**Full length form**
```
def foo() -> ():
    y: u256 = 1
    return ()
```

**No explicit return in signature**
```
def foo():
    y: u256 = 1
    return ()
```

**No explicit return statement**
```
def foo() -> ():
    y: u256 = 1
```

**No return in signature and function body**
```
def foo():
    y: u256 = 1
```

*Note that empty tuple literals are not supported yet, so some of the examples will not compile.*

Semantically, this is how Rust treats empty function returns. The reason why we followed suit is because it makes code more straight forward and saves us from having to implement a special type for empty function returns. Functions simply always return *something* even if this *something* means it's the `()` type.

## String and dynamically-sized ABI type support

Support for encoding of dynamically-sized arrays was prioritized this month so that we could implement strings, which are used in the ERC-20 contract. Although strings are encoded dynamically, their sizes are capped by the developer. In practice, these sizes look similar to the sizes of numeric types (e.g. `u8`, `u16`, .., `u256`). With strings, though, the size is representative of bytes and is not limited to a set of predefined sizes, meaning the developer can specify any size (e.g. `string32` or `string5555`).

Here's a piece of working Fe code that shows strings in action:

```python
contract Foo:
    event MyEvent:
        text: string100
        amount: u256

    pub def bar(text: string100, amount: u256):
        emit MyEvent(text, amount)
```

## Miscellaneous features

There's a whole bunch of features that weren't yet supported four weeks ago. Without going into too much detail, let's just list them here:

- Function calls (with or without arguments)
- If / Else statements
- While Loops (including `break` and `continue` statements)
- Boolean support
- Assert statements
- Events with multiple parameters
- Many improvements to our ABI encoder

### Final words

There's been a lot more development that didn't get mentioned here, but we'd like to keep these updates short and crisp. Maybe just a short teaser, [fe.ethereum.org](https://fe.ethereum.org) has been set up and currently refers to the generated API docs, but will be replaced by a proper website soon.