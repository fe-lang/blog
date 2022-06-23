+++
title = "Fe Development Update #3"
date = "2021-02-10"
+++


Howdy, this is our first development update in 2021. We would once again like to keep you up to date about all the progress that happened since [the previous update](https://snakecharmers.ethereum.org/fe-development-update-2/).


## We shipped v0.1.0-alpha "Amethyst"

Earlier this year, we landed our first alpha release with binaries for Linux and Mac. If you are as excited about Fe as we are, you might want to grab a binary from [here](https://github.com/ethereum/fe/releases/tag/v0.1.0-alpha) and play with some examples.

What's especially exciting about this release is that it has kicked of a fixed release cycle that we have committed to. From now on, we'll be shipping one release per month.

Just keep in mind that these are all **alpha** releases and are not supposed to be used for real world development just yet. Fe still has a long way to go before it can be used in production, but the pace of development is promising.

## More user-defined types

We now support two new type definitions -- structs and contracts. 

### Structs

Structs are a group of named variables in one segment of memory. They help with writing organized and efficient code.

For now, Fe only supports structs consisting of base types, this will be changed to include all types in a later version.

Example usage of a struct:

```python
struct House:
    price: u256
    size: u256
    vacant: bool

contract Foo:
    pub def bar() -> u256:
        building: House = House(300, 500, true)
        assert building.size == 500
        assert building.price == 300
        assert building.vacant

        building.vacant = false
        building.price = 1
        building.size = 2

        assert building.vacant == false
        assert building.price == 1
        assert building.size == 2
        return building.size

```

Usage of structs in Fe is pretty run-of-the-mill, so we won't go into too much detail describing the code above.

Further down the road, we intend to support function definitions on structs.

### Contracts

Fe of course already allows you to define contracts, but it wasn't until recently that contracts became types in their own right.

Now, if a contract definition is in the module scope, it can be used to conveniently deploy, load, and interact with contracts. Below is an example of a contract being loaded and called:

```python
contract Foo:
    event MyEvent:
        my_num: u256
        my_addrs: address[5]
        my_string: string11

    pub def emit_event(
        my_num: u256, 
        my_addrs: address[5], 
        my_string: string11
    ):
        emit MyEvent(my_num, my_addrs, my_string)

contract FooProxy:
    pub def call_emit_event(
        foo_address: address,
        my_num: u256,
        my_addrs: address[5],
        my_string: string11
    ):
        foo: Foo = Foo(foo_address)
        foo.emit_event(my_num, my_addrs, my_string)
```

Here an address is being cast to an instance of `Foo` and called using the attributes of `foo`.

We can also create new contracts, like so:

```python
contract Foo:
    pub def get_my_num() -> u256:
        return 42

contract FooFactory:
    pub def create_foo() -> address:
        # value and salt
        foo: Foo = Foo.create(0)
        return address(foo)
```

## Introducing `to_mem()` and `clone()`

These two builtin functions have been added for convenience when dealing with reference types. Here we'll explain why they were added and how to use them.

To understand what `clone()` does, consider the following example:

```python
pub def example(my_array: u256[10]):
    # assign my_array to another reference
    second_reference: u256[10] = my_array

    # Both variables point to the same section in memory
    assert my_array[3] == 5
    assert second_reference[3] == 5

    # Changing the 3rd item in second_reference also affects my_array
    second_reference[3] = 50
 
    assert my_array[3] == 50
    assert second_reference[3] == 50
```

As you can see, assigning a reference type to another variable does not copy the underlying data, it only creates a second variable that points to the same place in memory. This may not be what we want, though. We may want two distinct copies of the underlying data. In these situations, we can use `clone()` to copy the value to a new segment of memory. This is demonstrated in the following example:


```python
pub def example2(my_array: u256[10]):
    # clone my_array into second_array
    second_array: u256[10] = my_array.clone()

    # Both variables hold identical data to begin with
    assert my_array[3] == 5
    assert second_array[3] == 5

    # But changing the 3rd item in second_array does NOT affect my_array
    second_array[3] = 50
 
    assert my_array[3] == 5
    assert second_array[3] == 50
```


Now that we understand `clone()`, let's talk about `to_mem()` for a minute. In the first example, we said that `second_reference: u256[10] = my_array` creates a second reference to the same point in memory without copying the underlying data. This only works for reference types in **memory**, not **storage**. Consider this other example which **won't compile**.

```python
pub def example4():
    # THIS DOES NOT COMPILE
    second_array: u256[10] = self.my_array
```

The reason this code 👆 doesn't compile is because Fe won't let variables hold mutable storage pointers. This is on purpose. State mutation should be explicit in Fe, so we limit the places where state mutation takes place to statements that begin with `self` (e.g. `self.my_array[1] = 1` or `self.mutate_me()`). If we were to have mutable storage pointers running around in variables, someone could mutate state in a statement like `my_array[42] = 26`, which can make the contract's behaviour difficult to understand.

*Note: For now, all storage pointers are considered mutable, so the assignment rule described above currently applies to all storage pointers. In future versions of Fe, we will likely add Rust-style variable mutability, making it possible to assign storage pointers (as long as they're immutable).*

There are of course instances, though, where one would like to assign data found in storage. Since the only assignable pointer location is memory, we must copy values from storage and into memory before assigning them. To accomplish this, we provide the builtin function `to_mem()`. The `to_mem()` function is similar to `clone()`, but is used to copy values that are in storage to memory.

In the example below, we demonstrate how `to_mem()` can be used to pass an array held in storage into a function:

```python
pub def example3():
    self.my_function(self.my_array.to_mem())
```

For more information about how we plan on dealing with pointer locations in Fe, checkout [RFC #161](https://github.com/ethereum/fe/issues/161).

---

Whew! This was a lot to unpack. Here are a few more contributions we'd like to mention:

- Support for compiling modules with multiple contracts ([See PR#197](https://github.com/ethereum/fe/pull/197))
- Support for many builtin attributes (e.g. `block.timestamp`, [See PR#208](https://github.com/ethereum/fe/pull/208))
- CLI output can be overwritten via `--overwrite` ([See PR#206](https://github.com/ethereum/fe/pull/206))
- Support for static strings (e.g `val = "foo"`) ([See PR#182](https://github.com/ethereum/fe/pull/182))
- Lots of fixes and type safety improvements
- A number of bugs have been identified by [Alex Groce](https://github.com/agroce) using [afl-compiler-fuzzer](https://github.com/agroce/afl-compiler-fuzzer)

If you like to learn more about these, reading the linked Pull Requests should be a good start.

## What's next

We continue to work against our current target: Having a working Uniswap demo written in Fe. Building examples of real world Ethereum applications helps us to prioritize important features. If you are interested in tracking our progress you might want to checkout our [Uniswap demo milestone on Github](https://github.com/ethereum/fe/milestone/4).


### Special thanks

We would like to thank our new contributors Sean Billig, Volodymyr Lykhonis, Satyam Agrawal and Alex Groce who all did amazing work with their issues and pull requests that helped us move Fe forward.