
+++
title = "Rewriting the Ethereum Deposit Contract in Fe"
date = "2026-06-01"
+++

In this post we are going to look at one of Ethereum's most fundamental contracts: the deposit contract. We will briefly
review the contract's purpose and functionality, and then we will attempt to implement it in Fe. We want to set some constraints for ourselves to make this more interesting:

 - we want the contract to be written in a high-level style, without having to deal with low-level memory management or EVM details
 - we want the contract to be readable and concise
 - we want to beat the Solidity implementation in terms of gas cost, obviously

Ready? Grab your coffee and let's dive in!

## What is the deposit contract?

The deposit contract is the bridge between the execution layer and the consensus layer in Ethereum. For those who want to run a validator, they need to deposit 32 ETH into this contract and provide some information such as their public key of the validator and their withdrawal credentials. The deposit contract maintains a merkle tree of all deposits and generates deposit events that the consensus layer can listen to and activate the corresponding validators.

## Implementing the deposit contract in Fe

### The `DepositMsg` msg

Contracts in Fe follow a message-based programming model. Instead of contracts having functions that can be called, they receive messages, and the contract's behavior is defined by how it handles those messages. Not only does this resemble the way the EVM works under the hood, with messages being the fundamental unit of interaction, but it also enables a more powerful programming model for Fe that we will explore in future posts.

For now, let's define the `DepositMsg` with the four variants that we need to implement the contract's exposed functionality: `Deposit`, `SupportsInterface`, `GetDepositRoot`, and `GetDepositCount`. Each variant has a selector that defines how it can be called from the outside, and the fields that it contains. The `Deposit` variant is the main one, which will be called when a user wants to make a deposit. The other three variants are for querying the contract's state.

```rust
msg DepositMsg {
    #[selector = sol("deposit(bytes,bytes,bytes,bytes32)")]
    Deposit {
        pubkey: Bytes,
        withdrawal_credentials: Bytes,
        signature: Bytes,
        deposit_data_root: Bytes32,
    },

    #[selector = sol("supportsInterface(bytes4)")]
    SupportsInterface { interface_id: Bytes4 } -> bool,

    #[selector = sol("get_deposit_root()")]
    GetDepositRoot -> u256,

    #[selector = sol("get_deposit_count()")]
    GetDepositCount -> Bytes,
}
```

>Note: the `sol` function in the selector attribute isn't some magical compiler trick. It's a real `const fn` [defined in the standard library](https://docs.fe-lang.dev/#std::abi::sol::sol/fn) that computes the 4-byte selector at compile time.


### Event and storage structs

Structs are the main way to define data structures in Fe. Just like in Rust, we can add functions via `impl` blocks and use generics and traits to create powerful abstractions. Structs are also a common way to define events and storage layouts in Fe. For a struct to be used as an event, it needs to implement the `Event` trait. Thankfully, we don't have to do this manually, instead we can annotate our struct with the `#[event]` attribute and have the compiler implement the trait for us.

```rust
#[event]
struct DepositEvent {
    pubkey: Bytes,
    withdrawal_credentials: Bytes,
    amount: Bytes,
    signature: Bytes,
    index: Bytes,
}
```

Unlike in Solidity, there's no global state in Fe that functions automatically have access to. Instead, we explicitly pass a *storage effect* into every function that wants to read or write storage and we have to declare the storage effect on the contract level. We also have to be explicit about our intentions about whether we want this to be readonly or mutable. A common way to deal with storage is to encapsulate coherent pieces of storage into a struct like our `DepositStore`.

```rust
struct DepositStore {
    branch: [u256; DEPOSIT_CONTRACT_TREE_DEPTH],
    deposit_count: u256,
    zero_hashes: [u256; DEPOSIT_CONTRACT_TREE_DEPTH],
}

pub contract DepositContract uses (ctx: Ctx, mem: mut RawMem, log: mut Log) {
    mut store: DepositStore, // <-- this is where we make `DepositStore` available as a mutable storage effect
    // Rest of the contract omitted
}
```

### Accepting deposits

The main job of the deposit contract is to accept deposits and maintain the merkle tree of deposits. Our Fe implementation is a line-by-line translation of the equivalent Solidity code but uses higher-level abstractions where possible. Since Fe ships with a real standard library (written in Fe of course) we can import a few handy things from `ssz` to help us with the ssz based hashing and serialization that the deposit contract relies on. 

The first chunk of code is the validation of the input data. We also recompute the `deposit_data_root` from the input data and check that it matches the one provided by the user. It's very important to fail early and with clear error messages if the input data is invalid to prevent users from losing their funds by sending a malformed deposit. Please note that we intentionally implemented `compute_deposit_data_root` as a free floating function because it comes in handy to also use it in our unit tests.

Next, we emit the `DepositEvent` with the relevant information about the deposit. This is how the consensus layer will be able to listen to new deposits and activate the corresponding validators.

Notice that in Fe we use the `log` effect to emit events and we can directly pass our `DepositEvent` struct to the `emit` function without having to worry about encoding it ourselves. Behind the scenes, the compiler generates the necessary code to implement the `Event` trait for our struct because we annotated it with `#[event]`.

Finally, we update the merkle tree with the new deposit. Because this updates the contract's state, we need to use the `store` effect that we declared on the contract level.

```rust
pub contract DepositContract uses (ctx: Ctx, mem: mut RawMem, log: mut Log) {
    mut store: DepositStore,

    init()
    uses (mut store, mut mem)
    {
        for height in 0 .. DEPOSIT_CONTRACT_TREE_DEPTH - 1 {
            let cur: u256 = store.zero_hashes[height]
            store.zero_hashes[height + 1] = ssz::hash_pair(left: cur, right: cur)
        }
    }

    recv DepositMsg {
        #[payable]
        Deposit { pubkey, withdrawal_credentials, signature, deposit_data_root }
        uses (mut store, ctx, mut mem, mut log)
        {
            assert!(pubkey.len == 48, "DepositContract: invalid pubkey length")
            assert!(withdrawal_credentials.len == 32, "DepositContract: invalid withdrawal_credentials length")
            assert!(signature.len == 96, "DepositContract: invalid signature length")

            let value: u256 = ctx.value()
            assert!(value >= ether(1), "DepositContract: deposit value too low")
            assert!(value % gwei(1) == 0, "DepositContract: deposit value not multiple of gwei")
            let deposit_amount: u256 = value / gwei(1)
            assert!(deposit_amount <= u64::MASK, "DepositContract: deposit value too high")
            // Truncating cast matches Solidity's `uint64(x)`. The assert above
            // guarantees no information is lost.
            let amount_gwei: u64 = deposit_amount.downcast_truncate()

            let mut node: u256 = compute_deposit_data_root(
                pubkey,
                withdrawal_credentials,
                signature,
                amount_gwei,
            )
            assert!(
                node == deposit_data_root.val,
                "DepositContract: reconstructed DepositData does not match supplied deposit_data_root",
            )

            // Emit DepositEvent (index is the pre-increment deposit_count).
            log.emit(
                DepositEvent {
                    pubkey,
                    withdrawal_credentials,
                    amount: ssz::serialize_u64(amount_gwei),
                    signature,
                    index: ssz::serialize_u64(store.deposit_count.downcast_truncate()),
                },
            )

            assert!(store.deposit_count < MAX_DEPOSIT_COUNT, "DepositContract: merkle tree full")
            store.deposit_count += 1

            let mut size: u256 = store.deposit_count
            for height in 0 .. DEPOSIT_CONTRACT_TREE_DEPTH {
                if size & 1 == 1 {
                    store.branch[height] = node
                    return
                }
                node = ssz::hash_pair(left: store.branch[height], right: node)
                size = size / 2
            }
            // Unreachable: the MAX_DEPOSIT_COUNT check above guarantees we exit
            // via the `size & 1 == 1` branch within DEPOSIT_CONTRACT_TREE_DEPTH iterations.
            assert!(false)
        },
        // Other message handlers omitted
    }
}


// Reconstruct the deposit-data SSZ root from its constituent parts. Exposed at
// module level so tests can precompute a valid `deposit_data_root` to pass in.
#[inline(always)]
pub fn compute_deposit_data_root(
    pubkey: Bytes,
    withdrawal_credentials: Bytes,
    signature: Bytes,
    amount_gwei: u64,
) -> u256
uses (mem: mut RawMem)
{
    assert!(withdrawal_credentials.len == 32)
    (
        ssz::hash_tree_root<ssz::ByteVector<48>>(pubkey),
        withdrawal_credentials.word_at(0),
        ssz::u64_chunk(amount_gwei),
        ssz::hash_tree_root<ssz::ByteVector<96>>(signature),
    )
        .merkleize()
}
```


### The other message handlers

For the sake of completeness, let's also look at the other message handlers that we need to implement. The `GetDepositRoot` handler computes the current merkle root of the deposits tree and returns it. The `GetDepositCount` handler returns the current number of deposits. Finally, the `SupportsInterface` handler checks if the contract supports a given interface id, which is a common pattern in Ethereum to allow for interface discovery.

```rust
GetDepositRoot -> u256 uses (store, mut mem) {
    let mut node: u256 = 0
    let mut size: u256 = store.deposit_count
    for height in 0 .. DEPOSIT_CONTRACT_TREE_DEPTH {
        if size & 1 == 1 {
            node = ssz::hash_pair(left: store.branch[height], right: node)
        } else {
            node = ssz::hash_pair(left: node, right: store.zero_hashes[height])
        }
        size = size / 2
    }
    // Finalize with SSZ mix-in-length over `deposit_count`.
    // MAX_DEPOSIT_COUNT = 2**32 - 1 means the truncating cast never
    // loses information.
    ssz::mix_in_length(root: node, len: store.deposit_count.downcast_truncate())
}

GetDepositCount -> Bytes uses (store, mut mem) {
    let count: u64 = store.deposit_count.downcast_truncate()
    ssz::serialize_u64(count)
}

SupportsInterface { interface_id } -> bool {
    interface_id.val == 0x01ffc9a7 || interface_id.val == 0x85640907
}
```

### Gas cost and bytecode size comparison

By now, you might be wondering how our Fe implementation compares to the Solidity one in terms of bytecode size and gas cost. We ran both implementations through a series of tests and benchmarks and here are the results:

```
bytecode size
path         fe-O2        sol     sol-IR    fe vs sol-IR
------------------------------------------------------------
init          4091       4819       3082  +1009 (+32.7%)
runtime       3992       4445       2844  +1148 (+40.4%)

deployment gas
path        fe-O2        sol     sol-IR      fe vs sol-IR
-------------------------------------------------------------
deploy    1611141    1738847    1379411  +231730 (+16.8%)

call gas
path                            fe-O2        sol     sol-IR    fe vs sol-IR
-------------------------------------------------------------------------------
supportsInterface(erc165)       21600      21603      21600      +0 (+0.0%)
supportsInterface(deposit)      21600      21641      21600      +0 (+0.0%)
supportsInterface(unknown)      21600      21641      21600      +0 (+0.0%)
get_deposit_root(empty)        104238     117558     109178   -4940 (-4.5%)
get_deposit_count(empty)        23608      24510      24099    -491 (-2.0%)
deposit#0                       79946      84626      81089   -1143 (-1.4%)
get_deposit_root(after#0)      104258     117570     109174   -4916 (-4.5%)
get_deposit_count(after#0)      23608      24510      24099    -491 (-2.0%)
deposit#1                       65366      70411      66629   -1263 (-1.9%)
get_deposit_root(after#1)      104258     117570     109174   -4916 (-4.5%)
get_deposit_count(after#1)      23608      24510      24099    -491 (-2.0%)
deposit#2                       45734      50414      46877   -1143 (-2.4%)
get_deposit_root(after#2)      104278     117582     109170   -4892 (-4.5%)
get_deposit_count(after#2)      23608      24510      24099    -491 (-2.0%)
TOTAL                          767310     838656     792487  -25177 (-3.2%)
```

As we can see from the results, the Solidity optimizer still does a better job at shrinking the bytecode size for the deployment. However, in terms of gas costs on the actual contract interactions, the Fe implementation beats the most optimized Solidity version by a few percent.

## Conclusion

In this post, we implemented the Ethereum deposit contract in Fe and compared it to the Solidity implementation. You can find the full code of our implementation in our [GitHub repository](https://github.com/argotorg/fe/blob/2876e965e42187af6dd3a3a72978d35393f5e57b/crates/fe/tests/fixtures/fe_test/deposit_contract.fe).

We saw that Fe allows us to write high-level, readable, and concise code while still being competitive in terms of gas costs. This is just the beginning of what we can do with Fe, and we are excited to explore more complex contracts and applications in future posts. Stay tuned!