
+++
title = "Simple DAO written in Fe, go break it!"
date = "2023-11-08"
+++


With devconnect just around the corner, we would like to present another bug bounty opportunity.

Inspired by the original [Gnosis Multisig Wallet](https://github.com/OpenZeppelin/gnosis-multisig/blob/master/contracts/MultiSigWallet.sol), we have written a very simple DAO contract in Fe. It can be understood as a weighted multisig wallet where the execution of transactions is determined by a group of members and their voting power measured in governance tokens. To fully understand the concept we recommend to check out the [README](https://github.com/cburgdorf/simple_dao/blob/master/README.md) and the [source code](https://github.com/cburgdorf/simple_dao/tree/master/fe_contracts/simpledao/src).

We've deployed [an instance of the DAO](https://etherscan.io/address/0xf0adbb9ed4135d1509ad039505bada942d18755f) and its [governance token](https://etherscan.io/address/0xbb391A44dD49D7db376F8b50011ab5DaDEA6CBbA) on mainnet, set up members and funded it with some ETH. We've also had it [trade some of that ETH for RETH](https://etherscan.io/tx/0xe9dc0280d5472c241e76973c8e98621bce0b298bd46efc1c61cd12bbbed71471).

Unfortunately, Etherscan doesn't yet support source code verification for contracts written in Fe but we can verify the contracts ourselves with the latest release of [Fe 0.26.0](https://github.com/ethereum/fe/releases/tag/v0.26.0).

Here are the steps to do that:

1. Install the latest version of Fe (0.26.0) by following the [installation instructions](https://fe-lang.org/docs/user-guide/installation.html)

2. Clone the [SimpleDAO repository](https://github.com/cburgdorf/simple_dao/)

3. Checkout the `SimpleDAOBountyDeployment` tag to ensure to test the exact same version of the contracts that are deployed on mainnet

4. Navigate to `fe_contracts/simpledao`

5. `fe verify 0xf0adbb9ed4135d1509ad039505bada942d18755f https://eth.public-rpc.com`

The output should look like this:

```shell
It's a match!✨

Onchain contract:
Address: 0xf0adbb9ed4135d1509ad039505bada942d18755f
Bytecode: 0x60008..76b90

Local contract:
Contract name: SimpleDAO
Source file: /path/on/your/machine/to/simple_dao/fe_contracts/simpledao/src/main.fe
Bytecode: 0x60008..76b90`
```

Feel free to repeat step 5 with the address of the governance contract.

We invite everyone to try to hack the DAO and steal any money that is under the control of the DAO. We are also thinking about adding certain conditions (e.g. DAO balance drained to 0 ETH) to our [existing bug bounty platform](https://blog.fe-lang.org/posts/bountiful-round-2/) so that a successful hack of the DAO would be additionally be rewarded with the jackpot of the bountiful platform. For now, you can take our word for it that if you manage to hack the DAO, you'll be manually rewarded with another 3 ETH paid by us.

