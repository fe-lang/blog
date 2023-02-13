+++
title = "bountiful: round #2"
date = "2023-01-11"
+++

**UPDATE, Feb 13, we've activated two more challenges listed below**

We are happy to inform that we just activated the second round of our bountiful bug bounty contest. Make sure to read the [initial announcement](https://blog.fe-lang.org/posts/bountiful-break-things-and-get-paid/) if you aren't yet familar with the project.

### Before you hack

Before you get going, please take a minute to help us gather some feedback about our bug bounty contest through our [one minute survey](https://docs.google.com/forms/d/e/1FAIpQLScWytmjTEJCYCPXzxKnpS44vuPEuLku5KjSXD2LjmW4jiGLRA/viewform).

### Changes

After the first round [got exploited](https://twitter.com/plotchy/status/1600894668304105474) we fixed the (stupid!) bug, made a few smaller tweaks and have now redeployed the whole system.

We have also created two more game implementation. ~~but for now we decided against activating these just yet. Instead we decided to let some time pass with the existing code challenges and activate the new ones after enough time passed without someone having managed to find any exploits.~~ We deployed these two extra challenges after one month passed without the existing contracts getting exploited.

We have also lowered the lock deposit amount from 1 to 0.1 ETH because that should still be enough for the front running protection scheme to work and at the same time be more inclusive to hackers around the world.

### Addresses of deployed mainnet contracts

These are the addresses of the contracts that were deployed on the Ethereum mainnet. We also provide links to the tagged bountiful code that was used for the deployment. Please note that Etherscan doesn't yet support Fe source code verification which means that there is no code visible for these contracts at Etherscan. If you like to see Fe support on Etherscan, please [reach out to them and let them know](https://etherscan.io/contactus).

Registry contract: [`0x76eB86d4f92901f2af0d10feDDdA0B3B4630700D`](https://etherscan.io/address/0x76eB86d4f92901f2af0d10feDDdA0B3B4630700D) ([source code](https://github.com/fe-lang/bountiful/blob/0.2.0/contracts/src/registry/registry.fe))

Game contracts:

- 15 Puzzle implementation 1: [`0xD1175C6640A11bE625A53C8dc37ECAaC63A5d4f7`](https://etherscan.io/address/0xD1175C6640A11bE625A53C8dc37ECAaC63A5d4f7) ([source code](https://github.com/fe-lang/bountiful/blob/0.2.0/contracts/src/challenges/game.fe))
- 15 Puzzle implementation 2: [`0x0A4A0FA3dD290044FDdf9F0e8cFaf7f2A21443e4`](https://etherscan.io/address/0x0A4A0FA3dD290044FDdf9F0e8cFaf7f2A21443e4) ([source code](https://github.com/fe-lang/bountiful/blob/0.2.0/contracts/src/challenges/game_i8.fe))
- 15 Puzzle implementation 3: [`0x16ceA9A8D5E869F5FCD9504bea48000618a7e97c`](https://etherscan.io/address/0x16ceA9A8D5E869F5FCD9504bea48000618a7e97c) ([source code](https://github.com/fe-lang/bountiful/blob/0.2.0/contracts/src/challenges/game3.fe))
- 15 Puzzle implementation 4: [`0x8b36dfB5F1F9F3B1Bf1B2b2ADa63914016A49c60`](https://etherscan.io/address/0x8b36dfB5F1F9F3B1Bf1B2b2ADa63914016A49c60) ([source code](https://github.com/fe-lang/bountiful/blob/0.2.0/contracts/src/challenges/game3.fe))

**NEW, Feb 13**

- 15 Puzzle implementation 5: [`0x7Bd3ad385ac3354Cd9AB400F08076f0c10ebAD12`](https://etherscan.io/address/0x7Bd3ad385ac3354Cd9AB400F08076f0c10ebAD12) ([source code](https://github.com/fe-lang/bountiful/blob/master/contracts/src/challenges/game5_6.fe))
- 15 Puzzle implementation 6: [`0xA6b95deeba0089bc3d6689805179d439f714f2ed`](https://etherscan.io/address/0xA6b95deeba0089bc3d6689805179d439f714f2ed) ([source code](https://github.com/fe-lang/bountiful/blob/master/contracts/src/challenges/game5_6.fe))


### How to start

If you don't know how to get started, make sure to read the [initial announcement](https://blog.fe-lang.org/posts/bountiful-break-things-and-get-paid/), it contains all the needed information and is kept up to date.