
+++
title = "Fe 26.1.0"
date = "2026-04-30"
+++

The Fe team is happy to anounce the release of Fe 26.1.0!

This release contains a lot of internal work and bug fixing, along with some new functionality.
Highlights are below; full changelog is here: [v26.1.0](https://github.com/argotorg/fe/releases/tag/v26.1.0)

## Static assertions

Static assertions allow you to check the result of a compile-time computation.

```rust
const fn bps_amount(amount: u256, bps: u16) -> u256 {
    amount * (bps as u256) / 10_000
}

const fn apply_fee(amount: u256, fee_bps: u16) -> u256 {
    amount - bps_amount(amount: amount, bps: fee_bps)
}

const fn min_amount_out(quote: u256, slippage_bps: u16) -> u256 {
    quote - bps_amount(amount: quote, bps: slippage_bps)
}

static_assert(bps_amount(amount: 1_000_000, bps: 250) == 25_000)
static_assert(apply_fee(amount: 1_000_000, fee_bps: 30) == 997_000)
static_assert(min_amount_out(quote: 1_000_000, slippage_bps: 50) == 997_000)
```

When an assertion fails, it's reported as a compilation error:
```
error[8-0081]: static assertion failed
   ┌─ src/bps.fe:17:15
   │
17 │ static_assert(min_amount_out(quote: 1_000_000, slippage_bps: 50) == 997_000)
   │               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^ `static_assert` evaluated to `false`
   │
   = left: `995000`
   = right: `997000`
   = operator: `==`
```

## Increased `const fn` functionality

`const` functions can be executed at compile time when all the arguments are known.
This is useful for replacing hardcoded constants with
the function calls that generate them, without paying any runtime cost. `const`
functions are now much more powerful, supporting mutable locals, assignments, aggregate field and index writes, `while` and `while let` loops with `break` and `continue`, match/destructuring patterns, and const operator trait implementations.

To demonstrate this, we'll use snippets from a test case that generates poseidon hashes at compile time. Many details are omitted; the full file is here: [const_poseidon.fe](https://raw.githubusercontent.com/argotorg/fe/a6b13915fe59c8f292fc7a6a56e9308a6235adb0/crates/fe/tests/fixtures/fe_test/const_poseidon.fe).

First, we define a wrapper type that allows us to overload the `+` and `*` operations to mean field addition and field multiplication modulo the BN254 scalar field, to avoid noisy function calls. To do this, we implement the `Add` and `Mul` traits defined in the `core` library. If we define the `add` and `mul` implementations to be `const fn`, they can be executed at compile time. We also define other methods on `Fr` to be `const fn`.

```rust
struct Field {
    value: u256,
}

impl Add for Field {
    const fn add(own self, _ other: own Field) -> Field {
        Field::new(addmod(self.value, other.value, BN254))
    }
}

impl Mul for Field {
    const fn mul(own self, _ other: own Field) -> Field {
        Field::new(mulmod(self.value, other.value, BN254))
    }
}

impl Field {
    const fn pow5(self) -> Field {
        // `*` here calls the `mul` fn above
        let x2 = self * self
        let x4 = x2 * x2
        x4 * self
    }
}
```

This is the core Poseidon round logic, demonstrating the use of mutation and looping.
```rust
const fn permute3(mut state: own [Field; 3]) -> [Field; 3] {
    let mut round: usize = 0
    while round < POSEIDON_T3_ROUNDS {
        state = apply_round_constants3(state, round)
        state = apply_sbox3(
            state,
            full_round: is_full_round(
                round,
                half_full_rounds: POSEIDON_T3_HALF_FULL_ROUNDS,
                partial_rounds: POSEIDON_T3_PARTIAL_ROUNDS,
            ),
        )
        state = mix3(state)
        round += 1
    }
    state
}
```

`mix3` is the MDS matrix multiplication step; we initialize a mutable array to contain zeros, then we mutate the entries in a loop.

```rust
const fn mix3(state: [Field; 3]) -> [Field; 3] {
    let mut mixed: [Field; 3] = [Field::zero(); 3]
    let mut row: usize = 0
    while row < 3 {
        let mut col: usize = 0
        while col < 3 {
            mixed[row] = mixed[row] + state[col] * POSEIDON_T3_MDS[row][col]
            col += 1
        }
        row += 1
    }
    mixed
}
```

Here we define the hash function, and use `static_assert` to compare the result with that of a different implementation. All of this code can be used at run time as well, on dynamic values. If `hash2` is called with constant values within a runtime function, the Fe compiler will execute the code at compile time and insert the resulting value.

```rust
pub const fn hash2(left: u256, right: u256) -> u256 {
    permute3([Field::zero(), Field::new(left), Field::new(right)])[0].value
}

static_assert(hash2(0, 0)
    == 14744269619966411208579211824598458697587494354926760081771325075741142829156)
```

Note that `for` loops are not yet supported in `const` functions, but will be in a future release.

## Solidity-compatible errors

Solidity-compatible error types can now be defined with the `#[error]` attribute:

```rust
#[error]
pub struct SoldOut {
    pub requested: u256,
    pub remaining: u256,
}

fn mint(minted: u256, quantity: u256) -> Result<SoldOut, u256> {
    let remaining = 10_000 - minted

    if quantity > remaining {
        return Err(SoldOut {
            requested: quantity,
            remaining: remaining,
        })
    }

    Ok(minted + quantity)
}

#[test]
fn test_mint() {
    mint(minted: 9995, quantity: 100).unwrap()
}
```

`#[error]` gives `SoldOut` a selector and ABI encoding support. `.unwrap()` on the `Result` type
reverts with the error encoded in Solidity format: 4-byte selector followed by ABI-encoded
fields. This is equivalent to Solidity's `error SoldOut(uint256 requested, uint256 remaining)`.

Foundry will show a nice error if it knows the Solidity error signature:
`[FAIL: SoldOut(100, 5)]`
or just the selector otherwise:
`[FAIL: custom error 0x95d246db: ]`

`fe test` just dumps the payload (for now). This should certainly be improved.

```
FAIL  [0.0001s] test_mint
    Test reverted: 0x95d246db00000000000000000000000000000000000000000000000000000000000000640000000000000000000000000000000000000000000000000000000000000005
```

`revert_error(..)` can also be used:
```rust
use std::evm::revert_error

fn example() {
    revert_error(SoldOut { requested: 10, remaining: 0 })
}
```

## Solidity-compatible panic codes

Fe uses checked arithmetic by default; an overflow reverts, and now that revert carries the Solidity-compatible `Panic(uint256)` payload (0x11). Similarly, assertion failures are encoded as `Panic(0x01)`. The std lib now also defines `assert_msg`, which matches Solidity's `require(cond, message)` encoding (`Error(string)`).

```rust
#[test]
fn overflow() {
    let x: u8 = 255
    let y = x + 1
}

#[test]
fn math() {
    let x: usize = 1
    assert(x + x == 3)
}

#[test]
fn assert_with_msg() {
    assert_msg(false, "whoops")
}
```

Again, `fe test` will dump the ABI-encoded payload for now. Foundry and other tools will decode:
```
[FAIL: panic: assertion failed (0x01)]
[FAIL: whoops]
[FAIL: panic: arithmetic underflow or overflow (0x11)]
```

## Try it!

Fe 26.1.0 is available now for Linux, macOS, and Windows. Let us know what you think!

- **[fe-lang.org](https://fe-lang.org)**
- **[Write your first contract](https://fe-lang.org/getting-started/first-contract/)**: Get hands-on in minutes
- **[Zulip](https://fe-lang.zulipchat.com)**: Join the conversation
