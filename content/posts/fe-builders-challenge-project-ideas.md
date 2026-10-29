+++
title = "Fe Builders Challenge: Project Ideas"
date = "2026-10-29"
+++

The [Fe Builders Challenge](https://fe-lang.org/contest/) starts on
**November 3**. If you are still looking for an idea, this post is for you.
It is not a list of specifications. It is a collection of questions and
starting points, meant to send your own thinking somewhere new. The best
project is probably one we have not thought of.

Many of the sparks below start from something Fe makes easy that is hard
elsewhere: the same code can run in a contract and in a native program, every
function declares the capabilities it uses, and types can carry more meaning, such as
units or decimal scales.

## One codebase, on-chain and off-chain

Much of the Ethereum ecosystem runs next to the chain: keepers, solvers,
monitors, simulators. They need the same rules as the contracts they work
with, so the logic is usually written twice, once in Solidity and once in
whatever language the off-chain tool uses, and the two copies drift apart.

Since Fe 26.5, the release binaries also build native executables. Here is a
constant-product pool whose pricing is written once and used twice:

```rust
use core::fixed::Wad

const FEE: Wad = Wad::from_ratio(3, 1000)

// Constant-product pricing, written once.
pub fn amount_out(amount_in: Wad, reserve_in: Wad, reserve_out: Wad) -> Wad {
    let in_after_fee = amount_in * (Wad::one() - FEE)
    reserve_out * in_after_fee / (reserve_in + in_after_fee)
}

msg PoolMsg {
    #[selector = sol("swap(uint256)")]
    Swap { amount_in: u256 } -> u256,
}

// On-chain: the pool prices every swap with `amount_out`.
pub contract Pool {
    mut reserve_in: Wad,
    mut reserve_out: Wad,

    init() uses (mut reserve_in, mut reserve_out) {
        reserve_in = Wad::from_int(1000)
        reserve_out = Wad::from_int(1000)
    }

    recv PoolMsg {
        Swap { amount_in } -> u256 uses (mut reserve_in, mut reserve_out) {
            let input = Wad::from_raw(amount_in)
            let out = amount_out(amount_in: input, reserve_in, reserve_out)
            reserve_in = reserve_in + input
            reserve_out = reserve_out - out
            out.raw()
        }
    }
}

// Off-chain: replay thousands of swaps against the exact same pricing.
pub fn simulate(swaps: u256, size: Wad, reserve_in: own Wad, reserve_out: own Wad) -> Wad {
    var r_in = reserve_in
    var r_out = reserve_out
    var i: u256 = 0
    while i < swaps {
        let out = amount_out(amount_in: size, reserve_in: r_in, reserve_out: r_out)
        r_in = r_in + size
        r_out = r_out - out
        i += 1
    }
    r_out
}
```

`fe build` turns this file into the pool contract. `fe build --backend native`
turns the same file into a program whose `main` can run `simulate` over as
many scenarios as you like, and `fe test --backend native` runs your tests
natively. Change the fee or the curve, and the contract and the simulation
change together.

What else could live on both sides? A backtest of a lending market's
liquidation rules against years of price history. A game client that checks
moves with the code the contract runs. A tool that answers "what would happen
if" for thousands of states without asking a node, one call at a time.

## Rethink a protocol

You do not have to rebuild a protocol to rethink it. Many of the largest
protocols are designed to be extended, and Fe speaks their ABI: Solidity
structs such as Uniswap's `PoolKey` map directly onto Fe structs.

- **Uniswap v4** runs hooks around every swap. What would a fee, an order type,
  or a whole pricing curve look like if its units and decimal scales were part
  of the types?
- **CoW Protocol** lets a contract define orders that become valid when their
  conditions are met. If you could write any condition, which order would you
  place?
- **Safe** accounts can be extended with modules and guards. What should an AI
  agent be allowed to do with your money, and how could a reviewer see those
  limits at a glance?
- **Contracts behind a proxy** keep their storage when their implementation
  changes. Fe's standard library has the tools to work with Solidity's storage
  layout: `SolArray`, `SolEnumerableSet`, and the slot helpers in
  `std::evm::layout`. Which Solidity implementation would you replace with Fe,
  and how would you show that nothing changed but the code?

Or start from a blank page. Order books, auctions, lending, governance: every
handler in a Fe contract declares which storage it touches and whether it can
move funds. Which protocol would become easier to trust if that were visible
in its code?

## Make the math work

- **What could you prove?** Fe can compile programs for the
  [SP1](https://github.com/succinctlabs/sp1) zkVM, so a contract can accept the
  result of a computation that never ran on-chain. SP1 support is not in the
  release binaries yet; the
  [SP1 guide](https://github.com/argotorg/fe/blob/v26.5.1/tests/sp1/README.md)
  explains how to build the compiler with it.
- **What could you verify?** Pairings, SNARK proofs, Merkle-Patricia proofs of
  another contract's storage: the precompiles are wrapped in `std`, but most of
  the machinery around them is still waiting to be written.
- **What could you compute before deployment?** A `const fn` runs at compile
  time whenever its arguments are known, and the same function still works on
  runtime values. We have
  [computed Poseidon hashes this way](@/posts/release-26-1.md), and
  `static_assert` turns a wrong result into a compile error. Which lookup
  table, constant, or hard-coded magic number would you rather derive?
- **What could types protect?** Field elements that cannot be mixed up, points
  that cannot be passed as scalars, amounts that cannot be added to
  timestamps. Where does a type turn a subtle bug into a compile error?

## Build for the next builder

Think back to the last time you wrote Fe. What did you miss?

- **Native Fe is young.** There is a TOML parser
  ([lutz](https://github.com/fe-lang/lutz)) and a Keccak-256 library
  ([keccak](https://github.com/fe-lang/keccak)), but no JSON parser, no
  argument parser, and no client that talks to an Ethereum node. Native Fe can
  call C library functions, so even the network is within reach.
- **The standard library has gaps.** We have ported a lot from Solady and
  OpenZeppelin, and a lot is still missing. Which piece would you reach for
  first?
- **The tooling has gaps too.** `fe test` has no fuzzing. Fe can export
  experimental [ethdebug](https://ethdebug.github.io/format/) data, a
  starting point for debuggers and trace viewers. What would make the next
  developer faster?
- **How close can idiomatic Fe get to hand-written bytecode?** Which
  abstractions turn out to be free, and which do not?

Our own release notes are assembled by
[eisenbote](https://github.com/fe-lang/eisenbote), a port of towncrier written
in Fe. Which tool would you port?

## Take us by surprise

Games, art, agents, and experiments are welcome. A board game whose rules run
in a contract and in its client. A game with hidden information, where players
commit to their moves and reveal them later. A small world whose systems
declare which parts of it they may change. Art that a contract computes from
scratch, from a palette built at compile time to a physics simulation in
fixed-point arithmetic. Show us what Fe lets you express.

## Bring your own idea

If your idea fits none of the directions, that is fine: the only requirement
is that the core technical contribution is written in Fe. If you want feedback
on an idea or a sanity check on its scope, ask in the
[office-hours channel](https://fe-lang.zulipchat.com/#narrow/channel/594128-office-hours)
on Fe Zulip.

## Register by November 17

The build window runs from **November 3 to November 24**. Register your
project by **November 17**; your idea can still change after that. The
[starter repository](https://github.com/fe-lang/builders-challenge-starter)
gives you a tested Fe project, CI, and a README template, and the
[contest page](https://fe-lang.org/contest/) has the full rules.

**[Register your project](https://docs.google.com/forms/d/e/1FAIpQLSehDUUbqfQt67Ecy21zIsOFN7pp4orx9Ko9DKCWcDkjhEUVBg/viewform)**

Pick an idea, keep the scope small enough to finish, and show us what you
can build.
