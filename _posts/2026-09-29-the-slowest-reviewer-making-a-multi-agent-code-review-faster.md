---
date: 2026-09-29 18:00:00 +0800
layout: post
title: "Speeding Up a Multi-Agent Code Review in Claude Code"
slug: speeding-up-multi-agent-code-review-claude-code
subtitle: "Measure before you tune: model turns are the real clock, and parallelism stops at the rate limit."
description: >-
  Multi-agent code review in Claude Code: 114 runs showed model turns, not tools, were the bottleneck. What splitting agents, a call graph, and a 429 taught me.
image: https://images.unsplash.com/photo-1611147533125-9ca445f32036?q=80&w=2670&auto=format&fit=crop
optimized_image: >-
  https://images.unsplash.com/photo-1611147533125-9ca445f32036?q=80&w=800&auto=format&fit=crop
category: code
tags:
  - ai-agents
  - claude-code
  - code-review
  - multi-agent
  - performance
  - rate-limiting
author: yvetteTsai
paginate: true
---

My pre-PR code review in Claude Code isn't one agent. It's a small team: a scout that summarises the diff, seven specialist reviewers running in parallel (bugs, guidelines, history, prior art, comments, spec, design), and then one verifier per finding that tries to knock it down before it reaches me.

One reviewer was always last: the bugs reviewer. Everyone else would be done and waiting while it was still going.

I asked the obvious question: why is it slow, and can I make it faster? The answers were not what I expected.

## Lesson 1: measure first, from the logs you already have

Claude Code writes every subagent's transcript to disk, with timestamps, token usage, and every tool call. That meant I didn't have to guess. A short script over **114 past runs** of the bugs reviewer gave me a baseline:

| reviewer | median | p90 | turns |
|---|---|---|---|
| **bugs** | **157s** | **308s** | 18 |
| spec | 122s | 219s | 23 |
| history | 103s | 205s | 21 |
| guidelines | 73s | 161s | 15 |

My first guess was that the tools were slow: all that `grep`ing and `sed`ing around the codebase. It was wrong. Out of 1,284 shell calls, **one** took longer than ten seconds.

The time was going into **model round-trips**. The bugs reviewer made about 11 tool calls across 18 turns, almost always one call per turn. Each turn is a full round of the model thinking on the largest model tier, and that thinking costs 20 to 60 seconds. The tool call itself costs about one second.

![Sequence diagram: each turn the reviewer model thinks for 20 to 60 seconds, then makes one shell call that returns in about a second, repeated for about 18 turns]({{ site.baseurl }}/assets/diagrams/slowest-reviewer/turns.png)
*One tool call per turn: the thinking, not the tool, sets the pace. [Interactive version]({{ site.baseurl }}/assets/diagrams/slowest-reviewer/turns.html)*

> **Rule:** in an agent loop, the clock is the number of sequential turns, not the work done inside each one.

## Lesson 2: the slow agent was the one asked to leave the diff

The other reviewers mostly read the diff. The bugs reviewer's instructions asked it to go further:

- for every function the PR newly *calls*, read that function's body and check its assumptions still hold;
- check that no new import closes a cycle;
- follow any secret to every place it could leak (logs, exception text, `repr`, response bodies).

Each of those is "grep, read the result, decide the next grep". It's a chain of dependent lookups, and dependent lookups are serial turns.

So I made two structural changes:

1. **Split the agent in two.** `bugs` now reviews only the changed lines: logic, identity, degenerate input, fixes that are too broad. A new `reach` agent owns everything outside the diff. They run at the same time.
2. **Pre-compute the lookups.** Before the reviewers start, a script builds a call-graph digest of the diff with [GitNexus](https://github.com/abhigyanpatwari/GitNexus) and writes it to a file. It lists each changed symbol's callers, its callees, the *unchanged* functions the changed code calls, and any import cycles. The agents read one file instead of grepping their way to the same facts.

Two details mattered more than I expected:

- **Use the CLI, not the MCP server.** My review agents deliberately have no MCP tools, because MCP tool descriptions eat context before the agent reads a line of code. The GitNexus CLI (`analyze --index-only`, `cypher`, `check --cycles`) gives the same data through a plain shell script, and the agent just reads a text file.
- **The index has to match the code under review.** An index of `main` from yesterday describes the wrong code. The script refreshes the index of the review worktree first: about 30 seconds cold, a few seconds warm, in the background while the scout runs. So it costs nothing on the critical path.

One gotcha cost me an hour: the GitNexus CLI **truncates piped output at 64 KB**, because the process exits before the pipe drains. Writing stdout to a temp file fixed it. If a CLI's JSON comes back "unterminated", check the pipe before you check the parser.

The file also carries its own warnings, because static call graphs have blind spots. A call through a Protocol, a callback, or a registry is often missing, so an empty caller list is a lower bound, not proof there are no callers.

## Lesson 3: "batch your tool calls" is not an instruction the model follows

I also added a polite line to both agents: *collect everything you need, then fetch it all in one message with parallel tool calls.*

Then I measured the first real run, a 16,000-line diff split into seven slices:

| | calls per turn |
|---|---|
| old bugs reviewer | 1.05 |
| new bugs slices | 1.00 to 1.33 |

Essentially no change. The agents did chain commands with `;` inside a single shell call, which is half a batch, but they still thought, fetched, thought, fetched.

A suggestion didn't change the behaviour, so I rewrote it as a procedure with a violation clause: turn 1 reads every input in parallel; turn 2 lists every lookup and emits them all at once as separate tool calls; at most two more fetch turns after that; "a turn with a single tool call while more reads are foreseeable is a violation". Anything the agent couldn't afford to check goes into an `unverified:` list instead of being fetched one at a time.

I haven't measured that version yet. Prompts are hypotheses until the transcripts say otherwise.

--page-break--

## Lesson 4: splitting moves the bottleneck, it doesn't remove it

The good news: **a 16,000-line diff finished at all.** The old single reviewer had never run on anything over 6,000 lines. At that size it would likely have run out of context or taken a quarter of an hour. Seven slices in parallel meant the bugs stage took as long as the slowest slice, about seven minutes.

The less good news came in two parts.

**Per line, the new slices weren't faster.** Slices of 1,300 to 2,200 lines had a median of about 170 seconds. The old reviewer's median on diffs of 800 to 2,500 lines was 106 seconds. Smaller inputs don't help much when the cost is thinking per turn.

**The bottleneck moved.** I had sliced `bugs` seven ways but left `reach` as a single agent over the whole 16,000 lines. It became the longest-running agent: 31 serial turns, still going after six minutes, reading whole files. Every time you parallelise part of a pipeline, look at what's now at the back of the queue.

So `reach` gets sliced too, with the same groups. Each slice sees the whole diff for context but only reports problems that *start* in its own slice.

## Lesson 5: parallelism has a ceiling, and it's the API

Mid-run, the terminal started showing this:

```
429 {"detail":"Rate limited. Retry after 0.4s"} · Retrying in 17s · attempt 7/10
```

I had caused it. To make the review faster I'd also **pipelined the verifiers**: instead of waiting for all reviewers to finish, each reviewer's findings went to verifiers the moment it reported. Add seven bug slices and a `reach` agent, and the session peaked at **17 agents running at once**, 34 over the whole run. 26 of them hit a 429 at some point. One verifier that normally takes about 150 seconds took **621**, mostly waiting to retry.

Parallelism works until you hit the rate limit. Past that point, extra concurrency just turns into retry backoff.

The fix is a cap, not less parallelism:

- **at most 8 agents in flight**, reviewers and verifiers together;
- **one queue**: reviewers first, longest first (bug and reach slices, then the rest), verifiers behind any reviewer that hasn't started yet;
- **fewer, fatter slices**: at most three groups of 2,000 to 4,000 lines, so the two bug agents use at most six slots;
- if a 429 still shows up, drop the cap to 6 for the rest of the run.

![Workflow diagram: the scout builds a call-graph digest in the background; bugs, reach and five other reviewers run in parallel; all findings go into one queue capped at 8 agents, then one verifier per finding, then the report]({{ site.baseurl }}/assets/diagrams/slowest-reviewer/pipeline.png)
*The pipeline after all the changes: split reviewers, a pre-built call graph, and one capped queue. [Interactive version]({{ site.baseurl }}/assets/diagrams/slowest-reviewer/pipeline.html)*

I deliberately did *not* batch several findings into one verifier. The point of a verifier is an independent judgement of one claim. Grading a list invites the first answer to anchor the rest. I'd rather queue them than lose that independence.

Eight is a guess. The real limit depends on the account, and the next run will tell me whether it's right.

---

## The shared pattern

Every lesson here is the same one wearing different clothes: **the thing you think is expensive usually isn't.**

- I thought the tools were slow; it was the model's turns.
- I thought a smaller diff would make each slice faster; the cost was thinking per turn, not reading.
- I thought an instruction would change behaviour; the numbers said it didn't.
- I thought more parallelism was free; the API disagreed.

None of these were visible from the terminal. All of them were visible in the transcripts. The most valuable thing I built wasn't the call graph or the split agent. It was the fifty-line script that turned transcripts into a table, because it let me check every change against the old numbers.

---

## What's still open

- **The hard batching rule** is written and unmeasured. If calls per turn don't move off ~1.1, the next lever is fewer, deeper turns rather than more parallel calls.
- **The concurrency cap** of 8 is an estimate. One clean run without a 429 will confirm it; another 429 means 6.
- **Sliced `reach`** should remove the new bottleneck. The comparison to make is total review time on a similar-sized diff, not per-agent time.

The next large diff will answer all three. Until then, these are hypotheses, not results.
