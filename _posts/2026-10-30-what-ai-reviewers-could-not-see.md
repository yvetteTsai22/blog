---
layout: post
title: "Eight AI Reviewers, 45 Human Comments: What the Agents Couldn't See"
subtitle: "A prompt is a request. A tool boundary is a rule."
author: yvetteTsai
description: "Eight AI reviewers said clean; two humans left 45 comments. What AI review cannot see, and why most of the fix was writing rules down."
category: agents
image: https://images.unsplash.com/photo-1775163024488-e88e4a71179f?q=80&w=2670&auto=format&fit=crop
optimized_image: >-
  https://images.unsplash.com/photo-1775163024488-e88e4a71179f?q=80&w=800&auto=format&fit=crop
date: 2026-10-30 17:19:25 +0000
slug: what-ai-reviewers-could-not-see
tags:
  - ai-agents
  - claude-code
  - code-review
  - multi-agent
---

Eight AI reviewers said my PRs were clean. Two colleagues left 45 comments.

My pre-PR review in Claude Code runs eight specialist agents in parallel: bugs, reach, guidelines, history, prior art, comments, spec and design. Every finding then goes to a verifier that tries to knock it down. Only findings that survive with a score of 75 or more block the merge. Everything else is triaged as 🔴 blocker, 🟡 risk or 🔵 nit. Some PRs got a GitHub Copilot review on top.

On a good day the report says: 0 critical, 0 warnings, two blue nits. Branch marked clean. Then I asked two colleagues to review the same PRs.

The one that stopped me was small. *Don't put ticket numbers or history in code comments.* It showed up on almost every PR. My agents kept writing `// added for TICKET-123` and "previously this did X", and a colleague kept asking for it to be removed.

That's not a hard bug to catch. So why did eight reviewers and Copilot all miss it, every time?

I went looking for where the rule was written down. It wasn't in the repo's rules or in `CLAUDE.md`. It was a team habit that only existed in people's heads. Then I opened the decision log at the root of the repo. It had four entries, and nobody had added one for a while. We'd been shipping features faster than we wrote down why.

The agents weren't failing to follow the rule. Nobody had ever told them.

So I stopped asking how to make the agents faster ([I did that already]({{ site.baseurl }}/speeding-up-multi-agent-code-review-claude-code/)) and asked a different question: what were the humans seeing that the agents weren't?

--page-break--

## Sorting 45 comments into five piles

I pulled the feedback from 17 PRs and sorted every comment by *why* the agents missed it, not by what it was about. Five piles came out:

| pile | what it looks like | could an agent catch it? |
|---|---|---|
| calculation bugs | a task dispatched, blocked, then unblocked gets a *negative* queue time | yes, in principle, but only if it plays the timeline through instead of reading the diff |
| needs external data | a parity test that is skipped on every CI run, because CI has no database | no: the answer is in how CI runs, not in the repo |
| context gaps | "no ticket numbers in comments"; "moving a symbol means updating every caller, not leaving a re-export" | only if someone wrote it down |
| design issues | the same string format parsed in four places, twice in Python and twice in SQL | partly: it can flag it, a human decides |
| docs and style | user docs still describing the old UI | yes, and it mostly did |

The biggest pile by far was context gaps. They showed up on almost every PR, because the same unwritten rule got broken again each time.

The first and last piles are the agents' home ground. The middle three are the interesting ones, and they share a shape: the reviewer needed something the diff doesn't contain. That could be a timeline ("this ran last week, what happened?"), a second source to check against, or the reason behind a decision.

> **Rule:** AI review sees what's in the diff and what it is allowed to reach. Everything else is a blind spot, however many reviewers you run.

Eight agents reading the same diff are eight views of the same thing. Adding a ninth wouldn't have caught these.

The biggest pile, context gaps, doesn't need more reach. It just needs someone to write the rule down, and I'll come back to that at the end. What's left is the external-data pile, and that one does need the agents to reach outside the repo.

## The obvious fix, and why it's scary

If the blind spot is "can't reach outside data", the fix sounds simple: let the agents reach. Give them `gh` to read other PRs and issues, a shell to run queries, MCP tools to read tickets.

But a reviewer that can *read* GitHub through `gh` can also comment, approve, close and merge. A shell that can run a read-only query can also run anything else. And this pipeline runs eight agents at once, unattended.

My first attempt was the one everyone tries first. I wrote "you are read-only, do not modify anything" into each agent's instructions.

That's a request, not a rule. The model follows it most of the time. "Most of the time", across eight agents and every PR, means it will sometimes do the thing it was told not to.

To be honest, I never saw one of my reviewers try to write anything. That wasn't the point. The moment I planned to hand them `gh` and a shell, my first thought was *what if one of them edits something outside the repo?* I didn't want to find out the answer from a closed issue or a stray comment on someone else's PR. I wasn't willing to bet on "probably not".

## Moving the rule out of the prompt

So I moved the boundary out of the prompt and into the tools, in three layers:

1. **A read-only `gh` wrapper.** The agents don't get `gh`; they get `ro-gh`, which allows a whitelist of read subcommands and refuses everything else.
2. **A bash guard.** A small script that runs before every shell command and denies anything outside the allowed patterns. It has 38 tests: 14 commands it must allow and 24 it must deny. The deny list is the longer one on purpose.
3. **Tool restrictions per agent.** Each of the 10 agent definitions lists only the tools that agent needs. A reviewer with no write tool can't write, whatever it decides.

A fine-grained token would be a fourth layer. I didn't use one this time, because getting an org token approved would have taken longer than the rest of the change put together. That's a real gap, and I know it's there.

> **Rule:** a prompt is a request. A tool boundary is a rule. If breaking it would cost you, enforce it in code.

With the boundary in place, giving agents more reach stopped being scary. The "spec" and "reach" reviewers got new instructions to pull the outside context they'd been missing, through tools that can only read.

## The rule was in the wrong place

After sorting the comments, I did the boring fix for the biggest pile: I wrote the unwritten rules down. One line per rule, in a review-lessons file that every reviewer reads before it starts. The comment rule reads: *comments that narrate history ("previously", "used to", a bare ticket or PR id) instead of explaining the code as it is: history goes in the commit, not the comment.*

A few days later, on a new ticket, the review flagged a docstring that told the story of an old incident: *"…did exactly that, two minutes after it cloned."* Its reason was that rule. The comment my colleague had been repeating by hand was caught before anyone else saw the PR.

It wasn't perfect. One of the fixes it offered was "keep one line with the ticket number instead", which the rule it had just quoted rules out. Writing a rule down gets it *found*; it doesn't stop the agent from proposing the thing the rule forbids. A human still picks the fix.

The agents can now reach more external data than before, safely. Whether they use it well is the next experiment, and it's where I'm least sure.

And there's a bigger gap I only noticed while writing this. That lessons file lives in *my* setup, not in the repo. My reviewers know the rule now. My colleagues' agents don't, Copilot doesn't, and the decision log at the root of the repo still has four entries. I moved the knowledge out of people's heads and into my own tools, which is one step better than nowhere, and still not where the team can see it. The next step isn't a better reviewer. It's a habit: decisions go into the repo, in a place every agent and every person reads.

> **Rule:** when a human reviewer keeps leaving the same comment, it's usually not a review problem. It's a rule that was never written down.

If you run AI review on your PRs, try this: take the last 20 comments a human left that your agents didn't, and sort them by *why* they were missed. My guess is that most of your piles won't be about the model at all.

What's the review comment your team keeps leaving that no agent has caught yet? I'd love to hear it.
