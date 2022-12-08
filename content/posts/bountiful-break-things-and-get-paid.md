+++
title = "bountiful: break things and get paid"
date = "2022-12-06"
+++

**UPDATE: Someone was lucky enough to already take the bounty. Here's [a short twitter thread explaining what happened](https://twitter.com/official_fe/status/1600810003253719040).
We will restart the contest soon!**

Today we are unveiling the *bountiful* project. It is - to our knowledge - the first Fe code deployed to the Ethereum mainnet. This marks an important milestone for Fe on its road to become a production-ready EVM language.

### Introducing *bountiful*

As we mentioned before, one of the milestones on [Fe's path to production](https://blog.fe-lang.org/posts/path-to-production/) is hosting community bug contests. In this way we want to encourage the community to search for compiler bugs. The *bountiful* project is our initial effort to do this. Not only did we have a lot of fun trying out our own dogfood, we are also setting an example of how Fe can be used in a real mainnet project.

### How it works

At its core is a registry that lets us register bug bounty challenges. All these challenges have one thing in common, they can only be solved if one of the following conditions is met:

- a bug in the implementation of the code challenge was found and exploited
- a bug in the Fe language itself was found and exploited

To incentivize people to find these exploits the system lets the exploiter claim a bounty of ETH in a permissionless way. We are starting with a prize money of **3 ETH** which is subject to changes in the future.

Although we are mainly interested in discovering compiler bugs, exposing bugs in the implementation of any of the code challenges is also valuable, as these can provide important clues where the language should make it even harder to hide bugs.

### The challenges

While the system is designed to allow registering an unlimited number of challenges we are starting with **4** different implementations of the popular 15 puzzle. In case you've never played this before, [here's a link to a free online version of the game](https://15puzzle.netlify.app/). It's a frame with 16 squares and 15 movable tiles that need to be brought in order. What's interesting about this game is that there are certain game states that are impossible to solve. The games that we have deployed all start from such an unsolvable game state. That means that one can only win the game by exploiting a bug either in the implementation of the game or in the Fe language directly. For instance, imagine a bug that gives us unguarded access to modify the storage space of the game contract in unintended ways. If such a bug exists, someone could bring the game into the winning state essentially through bypassing the rules of the game.
Please note that these games were not written for gas efficiency, elegance or conciseness - quite the contrary. We have written them purposefully verbose to maximize the potential of exposing bugs. For the same purpose have we chosen to create multiple implementations of the same game so that we can exercise different approaches and language features.

### Frontrunning prevention

[Ethereum is a dark forest](https://www.paradigm.xyz/2020/08/ethereum-is-a-dark-forest) which is why we need a front-running prevention mechanism. In short, if it is possible to send a transaction that will make the sender richer (in our case by exploiting a Fe bug and claiming ETH prize money) we can be sure that somewhere there's a bot noticing it who will perform the same transaction faster leaving the honest claimer empty handed.

To avoid this we've come up with a very simple front-running prevention mechanism. Here is how it works:

1. As a bounty hunter we first try to find an exploit by attacking the contracts locally on our own development machine (more on that later)
2. Let's suppose we have found a way to bring the code challenge into its `solved` state on our own local machine
3. To replicate our success on the actual bug bounty registry and claim the prize we first have to aquire an exclusive lock via `registry.lock()`

Because it's fun to look at Fe code, here is how `lock` is implemented:

```rust
pub fn lock(mut self, ctx: Context) {
    if self.is_locked(ctx) {
        revert AlreadyLocked()
    } else if ctx.msg_value() < LOCK_DEPOSIT_IN_WEI {
        revert InvalidDeposit()
    } else {
        self.lock = ClaimLock(
            claimer:ctx.msg_sender(),
            valid_until_block: ctx.block_number() + LOCK_PERIOD_IN_BLOCKS
        )
    }
}
```

The `ctx` parameter is automatically provided for public contract functions and is Fe's way to provide access to various EVM features without relying on globals. It also makes it simple to see what kind of capabilities a function has just by looking at its signature while at the same time avoiding the introduction of unnecessary keywords. A function that doesn't take `self` nor `ctx` is obviously *pure*.

As we can see, an exclusive lock is provided if no one else currently holds a lock and if the minimum *lock deposit* is provided as the transaction value. The lock deposit is needed to prevent someone from repetitively acquiring locks to gain more time to find an exploit while simultaneously preventing others to claim the bounty. The lock deposit is paid back together with the actual prize money if a successful claim was made within the granted *lock period*. If the prize money is not claimed over the duration of the lock period the lock deposit will end up as extra money to grow the jackpot. 

4. Now that we have acquired an exclusive lock we have a window of `1000` blocks (roughly 3 hours) to bring *any* of the challenges into the *solved* state. Cautious as we are, we will wait a few more blocks before we present the solution.

5. Now it's time to solve one of the challenges, which means we exploit the contract in the same way that we have successfully done before on our local development machine. It is important to point out that no other party can interfere with any of the code challenges because we have obtained an exclusive lock.

6. Next we call `registry.claim(address_of_challenge)` to claim the prize money. Let's look at the implementation of `claim` as well.

```rust
pub fn claim(self, mut ctx: Context, challenge: address) {
    self.validate_owns_lock(ctx, owner: ctx.msg_sender())

    if not self.open_challenges[challenge] {
        revert InvalidClaim()
    } else {
        let puzzle: ISolvable = ISolvable(challenge)
        if puzzle.is_solved() {
            ctx.send_value(to: ctx.msg_sender(), wei: ctx.self_balance())
        } else {
            revert InvalidClaim()
        }
    }
}
```

Notice that `claim` also takes `ctx` as its second parameter but just like `self` it doesn't need to be provided by the external caller. Also notice the `mut` keyword before `ctx: Context`, that's because mutability is always *explicit* in Fe. This makes it very easy to see where changes are happening.

The first thing `claim` does is that it validates that the caller owns the lock. It then goes on to validate that the `challenge` address is indeed a registered challenge. It then goes on to call `is_solved()` on the challenge and pays out the prize money in case it returns `true`. In other words, getting `is_solved()` to return `true` is what is actually needed to win the money!

7. Profit! 💸

### I'm game! Where do we start?

So you want to crack the jackpot? Here's how it really works. We don't expect it to be easy. If someone manages to exploit the contracts they sure know what they are doing. They will know how to approach this and which tools to use. This is to say that we don't have much guidance on *how* to actually find an exploit (if ever!).

But still, here's a basic start

1. First, clone the [code from GitHub](https://github.com/fe-lang/bountiful)

2. Next, run `npx hardhat test`

This will execute all tests on all challenges as well as a bunch more tests on the registry directly.

Some of these tests can give us an idea how to win the game and claim the prize money but keep in mind that these tests start from an easily solvable game state which is not the case for the deployed live contracts.

A good starting point might be to generate and inspect the bytecode as well as the intermediate representation (in YUL) for any of the challenges via `fe build path/to/challenge.fe --emit yul,bytecode`.

In practice, finding a bug hopefully won't be as easy as calling one of the regular game APIs with regular input. If at all possible it will hopefully require real wizardry.

### Addresses of deployed mainnet contracts

These are the addresses of the contracts that were deployed on the Ethereum mainnet. We also provide links to the tagged bountiful code that was used for the deployment. Please note that Etherscan doesn't yet support Fe source code verification which means that there is no code visible for these contracts at Etherscan. If you like to see Fe support on Etherscan, please [reach out to them and let them know](https://etherscan.io/contactus).

Registry contract: [`0xcF19640dfB72762d6B75d6AfeEcFb5d54092f768`](https://etherscan.io/address/0xcF19640dfB72762d6B75d6AfeEcFb5d54092f768) ([source code](https://github.com/fe-lang/bountiful/blob/0.1.0/contracts/src/registry/registry.fe))

Game contracts:

- 15 Puzzle implementation 1: [`0x08554F7A7674841053d55f9ACe77D698FD25b99e`](https://etherscan.io/address/0x08554F7A7674841053d55f9ACe77D698FD25b99e) ([source code](https://github.com/fe-lang/bountiful/blob/0.1.0/contracts/src/challenges/game.fe))
- 15 Puzzle implementation 2: [`0x8e3C037b9f76DE7E1b094C6b7BEEa6e80dCB3f64`](https://etherscan.io/address/0x8e3C037b9f76DE7E1b094C6b7BEEa6e80dCB3f64) ([source code](https://github.com/fe-lang/bountiful/blob/0.1.0/contracts/src/challenges/game_i8.fe))
- 15 Puzzle implementation 3: [`0xa48607017E7E79011bb0C6B2cB2a462808015449`](https://etherscan.io/address/0xa48607017E7E79011bb0C6B2cB2a462808015449) ([source code](https://github.com/fe-lang/bountiful/blob/0.1.0/contracts/src/challenges/game3.fe))
- 15 Puzzle implementation 4: [`0x27BD48e8098aAf734005483E2cD4a029F70ADc0D`](https://etherscan.io/address/0x27BD48e8098aAf734005483E2cD4a029F70ADc0D) ([source code](https://github.com/fe-lang/bountiful/blob/0.1.0/contracts/src/challenges/game3.fe))

### Final words

Creating a new programming language takes a big effort. In an environment where potentially huge amounts of money rely on the safety of the language we have to be extra cautious before we encourage people to use Fe for the development of serious projects. All the more are we excited to be the first to deploy Fe code to mainnet with real money on the line. If you like Fe to succeed please share the word with colleagues and friends. Also please don't hesitate to [file bugs and feature requests](https://github.com/ethereum/fe/issues) or hop in our [discord](https://discord.gg/ywpkAXFjZH) for any feedback and questions.

Get the Jackpot anon!

