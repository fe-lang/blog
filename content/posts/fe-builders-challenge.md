+++
title = "Fe Builders Challenge: Build with Fe, Compete for $5,000"
date = "2026-10-27"
+++

What would you build with a fresh set of tools for the EVM?

The **Fe Builders Challenge** runs from **November 3 to November 24**: three
weeks to explore Fe, build something worth sharing, and compete for
**$5,000 in prizes**. Bring a protocol
you want to rethink, a library you wish existed, a cryptographic idea, or a game
you have been meaning to make.

Fe brings expressive types, generics, traits, and compile-time execution to EVM
development. [Fe 26.5](@/posts/release-26-5.md), our biggest release so far,
adds a simpler borrowing model, closures, typed ETH amounts, Solidity-compatible
storage, and a much larger standard library. The release binaries can now also
build native programs. This challenge is an invitation to put those capabilities
to work: build something useful, test an ambitious idea, or show a clearer way
to solve a familiar problem.

The contest is fully online, open to individuals and teams, and welcomes
first-time Fe developers. You have until **November 24** to finish your project.
Register it by **November 17** so we can check the details and reach you before
the final deadline.

## Dates at a glance

| Date | Milestone |
| --- | --- |
| November 3, 2026, 00:00 UTC | Build window opens. Start building. |
| November 17, 2026, 23:59 UTC | Project registration closes. |
| November 24, 2026, 23:59 UTC | Final submissions close. |
| November 25–December 1, 2026 | Eligibility checks, judging, and results preparation. |
| December 1, 2026 | Winners announced. |

## $5,000 in prizes

The [Argot Collective](https://argot.org) is funding a **$5,000 prize pool**, awarded to the top
three projects:

| Place | Prize |
| --- | ---: |
| 1st | $2,500 |
| 2nd | $1,500 |
| 3rd | $1,000 |

All eligible projects compete in the same pool, and all three prizes will be
awarded. Prizes are paid in USDC on Ethereum Mainnet to one payout address per
winning project; teams split their prize internally.

## What can you build?

Build something whose core technical contribution is written in Fe. Frontends,
scripts, agents, benchmarks, and other supporting components can use any
language. Projects can target the EVM or native code: since Fe 26.5, the release
binaries build native executables, so a developer tool written in Fe is just as
welcome as a smart contract.

Here are a few directions to get you thinking. They are inspiration, not
separate tracks, and you do not have to pick one.

### Rethink a protocol

Revisit an auction, exchange, governance mechanism, or another onchain system.
Can Fe make its implementation easier to understand, its assumptions more
explicit, or its code more reusable? Can you improve its runtime or gas usage?

Explain what changed and demonstrate the benefit with tests, benchmarks, code
comparisons, or a clear technical argument. A thoughtful redesign can be just
as interesting as a new mechanism.

### Build mathematical and cryptographic tools

Explore advanced arithmetic, proof verification, or reusable cryptographic
building blocks. Use types and abstractions to make complex code easier to
reason about. Make your assumptions explicit and include test vectors and
known limitations.

### Give the next Fe developer a head start

Build a library, a standard-library addition, or a developer tool with a
meaningful Fe component. A focused, well-tested library with a clear API can be
a strong submission. Standard-library work does not need to be merged upstream
before the deadline. Pure compiler contributions are outside this contest's
scope.

### Surprise us

Games, art, agents, social applications, and unusual experiments are welcome.
If you have an idea that does not fit the examples above, we want to see it.
Show us what Fe lets you express and why the result is interesting.

## How to take part

### 1. Start building on November 3

The build window opens on **November 3, 2026, at 00:00 UTC**. You do not need
to register before you begin, and you can explore Fe before the window opens. Start with the
[Fe documentation](https://fe-lang.org/) and the
[first-contract guide](https://fe-lang.org/getting-started/first-contract/).

**Contest toolchain:** Any Fe release from 26.5.0 on. Install it with feup as
described in the [installation guide](https://fe-lang.org/getting-started/installation/),
and state the exact version you used in your submission so the judges can
reproduce your work.

**Starter repository:** The
[builders-challenge-starter](https://github.com/fe-lang/builders-challenge-starter)
contains a small, tested Fe project, a CI workflow, the submission checklist,
and a template for your final README. Clone it to get going in minutes.

Existing projects may enter, but only substantial work completed during the
contest window will be judged. Clearly identify your starting point and what
you added or changed.

### 2. Register your project by November 17

Register by **November 17, 2026, at 23:59 UTC**. We ask for a project name,
a one-sentence idea, team members, and one responsible human contact we can
reach. Include a repository link if you already have one; a finished project
is not required.

Registration helps us resolve missing information before the final week. Your
idea can evolve as you build. Your confirmation
will explain how to update your details and make your final submission.

**[Register your project](https://docs.google.com/forms/d/e/1FAIpQLSehDUUbqfQt67Ecy21zIsOFN7pp4orx9Ko9DKCWcDkjhEUVBg/viewform)**

### 3. Submit your finished project by November 24

Final submissions close on **November 24, 2026, at 23:59 UTC**. Submit a public
GitHub repository and identify the exact commit the jury should review.

Include:

- An OSI-approved open-source license.
- Your project manifest, exact Fe version, and reproducible build and test instructions.
- Automated tests appropriate to the project.
- A README explaining the problem, your approach, how the code fits together,
  and any limitations.
- A one-sentence pitch and one Fe-specific technical highlight or code example.
- A short demonstration: a video, screenshots, or a reproducible CLI example,
  as appropriate for your project.
- A declaration of pre-existing work, reused third-party code, and AI assistance.

Mainnet deployment is not required and does not give a scoring advantage.
A testnet deployment is sufficient where a deployment helps demonstrate the
project.

**[Submit your project](https://docs.google.com/forms/d/e/1FAIpQLSd2pqUkJzFpZMu5FVQP-NtetrIoB6nI-pHG1MLTOQhCpsLKqg/viewform)**

Use the personalized submission link in your registration email to prefill your
project ID, private submission code, and contact email. If you use the link
above, enter those details yourself. Keep your submission code private.
You can submit again before the deadline; your latest valid submission counts.

**Full rules:** The [contest page](https://fe-lang.org/contest/) covers
eligibility, deadlines, judging, and prize payment.

## AI assistance is welcome

You can build solo, with teammates, or with AI agents. AI use is permitted and
is not scored negatively. Briefly describe how you used it, and make sure you
understand and can explain the resulting code. The jury may ask technical
questions about your submission.

We judge the project, regardless of the number of people or agents involved.
Each submission needs one responsible human contact for communication and
prize payment.

## Meet the jury

Eight judges will review the projects:

- **[Austin Griffith](https://x.com/austingriffith)**, BuidlGuidl, builder and educator
- **[Ahmed Castro](https://x.com/FilosofiaCodigo)**, Filosofía Código, developer and educator
- **[Marius van der Wijden](https://x.com/vdWijden)**, Ethereum Foundation, core developer
- **[Philogy](https://x.com/real_philogy)**, security researcher and creator of Plank
- **[Rahul Kothari](https://x.com/omw_to_the_moon)**, Ethereum Foundation, dev tooling lead
- **[jistro](https://x.com/jistro)**, EVVM, smart contract developer
- **[Grant Wuerker](https://github.com/g-r-a-n-t)**, Argot Collective, Fe core developer
- **[Micah Scopes](https://github.com/micahscopes)**, Argot Collective, Fe core developer

You can read more about each judge on the
[contest page](https://fe-lang.org/contest/).

## How projects will be judged

The jury will assess each project using the same public rubric:

| Criterion | Weight | What we are looking for |
| --- | ---: | --- |
| Technical quality and correctness | 30% | Sound implementation, appropriate tests, completeness, and clear security assumptions. |
| Fe-specific value | 25% | Meaningful use of Fe's language features, abstractions, or tooling. |
| Originality | 20% | A fresh idea, implementation, or combination. |
| Usefulness or insight | 15% | Value for users, developers, researchers, or future Fe projects. |
| Documentation and demo | 10% | Clear explanations and a result others can reproduce. |

The evidence should fit the project: a cryptographic library needs test vectors;
a claim about gas efficiency needs benchmarks; a developer tool needs a clear
workflow. Explain what your project demonstrates and give the jury a way to
verify it.

After eligibility checks, judges will review submissions independently. The
jury will then review a shortlist and select the three winners. Judges will
declare conflicts of interest and recuse themselves where necessary.

Judging takes place online over one week. We aim to announce the winners on
**December 1** on this blog and on X. The jury's decisions are final, and
individual feedback is not guaranteed. There is no public-vote component;
social reach does not affect your score.

## Get help as you build

Join us on **[Fe Zulip](https://fe-lang.zulipchat.com)** to ask questions, discuss
ideas, and share progress. You do not need previous Fe experience to take part.

**Contest discussion:** Ask questions in the
[office-hours channel](https://fe-lang.zulipchat.com/#narrow/channel/594128-office-hours)
on Fe Zulip. If something blocks your entry, email
[hello@fe-lang.org](mailto:hello@fe-lang.org).

Pick an idea, explore what Fe can do, and make something you want other
developers to try. **Three weeks. $5,000 in prizes. Show us what you can build.**
