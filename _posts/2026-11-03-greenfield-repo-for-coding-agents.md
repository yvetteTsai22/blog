---
layout: post
title: "Before the Agent's First Ticket: What We Put in an Empty Repo So It Wouldn't Go Wild"
subtitle: "Whatever you don't decide before the first ticket, the agent decides for you."
author: yvetteTsai
description: "Setting up a greenfield repo for a coding agent: what we committed before the first ticket so it wouldn't pick its own stack, and what that couldn't stop."
category: agents
image: https://images.unsplash.com/photo-1519143009590-e3800b9df468?q=80&w=2670&auto=format&fit=crop
optimized_image: >-
  https://images.unsplash.com/photo-1519143009590-e3800b9df468?q=80&w=800&auto=format&fit=crop
date: 2026-11-03 16:16:57 +0000
slug: greenfield-repo-for-coding-agents
tags:
  - ai-agents
  - multi-agent
---

Before the agent's first ticket, we were not worried that it would get stuck. We were worried that it would go wild.

Picture the repo from the agent's side. It clones, opens the root, and finds nothing. No framework to follow, no component to copy, no test to imitate. In an existing repo the agent copies your code. In an empty one, it falls back on its own defaults.

Its defaults are not your team's defaults. Ask for a GenAI feature and you may get raw `requests` calls to an LLM API instead of the framework your team uses. Ask for a screen and you get the generic AI-generated look, instead of the component library your front-end engineers know.

> **Rule:** Whatever you don't decide before the first ticket, the agent decides for you. If your repo doesn't name your team's LLM framework, whether it's LangGraph or ADK, and your component library, the agent will pick its own.

![An agent in an existing repo copies your conventions; in an empty repo it falls back to its defaults]({{ site.baseurl }}/assets/img/greenfield-repo-for-coding-agents/existing-vs-empty-repo.svg)

We were about to put an agent in exactly that repo. We run an in-house cloud coding agent: a ticket goes in, a PR comes out, a human reviews it. Until then it had only worked in repos that already had code. This time we wanted a pitch POC built from zero, as fast as possible. So before any ticket, we decided to commit a scaffold.

## Two commits before the agent touched anything

That was the whole human setup:

- a monorepo with the languages, package managers and versions pinned: Node and pnpm for TypeScript, Python and uv for the API
- lock files for both
- one command to set up and one to check (lint, format, typecheck), plus CI that runs it on every PR
- a design-system package with its own `AGENTS.md`
- a root `AGENTS.md` with a short list of hard rules
- the specs (story spec, system spec, a "current slice" doc) and seed demo data, committed to the repo

The rules in `AGENTS.md` were blunt:

- Use only the listed tools. Never npm or yarn, never pip or poetry.
- Read the slice doc first, on every ticket.
- Never edit the specs or the seed data.
- Build UI only from design-system components. If one is missing, add it to the design system.

Every rule maps to a choice the agent would otherwise have made by itself.

About an hour after the scaffold landed, the agent opened its first PR. By the end, 50 of its 53 PRs were merged.

The scaffold worked. To keep that from being a one-off, I went back through the repo afterwards and asked of each piece: why is this here, and did it have to be?

By the end it boiled down to six things. They spell a word worth checking before any first ticket.

## What each piece decides, so the agent doesn't

Here is where each piece comes into play during one agent run:

![One agent run, from ticket to human review, with the scaffold piece each step depends on]({{ site.baseurl }}/assets/img/greenfield-repo-for-coding-agents/agent-run-scaffold.svg)

Most of it was obvious. A few pieces were not what I assumed.

**The lock file isn't about speed.** I asked what I thought was a simple question: isn't the image built once and reused? Then a lock file only matters the first time.

That's not how it works. The image is reused, but every agent run starts in a fresh container and installs again. Without a lock file, every install resolves versions again. Two tickets on the same day can get different versions, and CI can get a third set. When a test goes red, you can't tell if it's the code or a package that shipped yesterday.

You can write the versions down in a spec. That only pins what you list.

> A spec can name the version. Only a lock file can freeze it.

**The warm image is what makes runs fast.** If you want speed, bake the dependencies into the agent's image. That doesn't replace the lock file: the image is a snapshot, the agent still resets to the latest branch, and CI doesn't use the image at all. **Warm image solves speed. Lock file solves consistency. You want both.**

**The specs belong in the repo.** Our agent runs in an isolated container with no access to our wiki. Plenty of agents can reach a wiki, a memory tool or a detailed ticket, and that context helps. But it is per ticket and it moves: one ticket links the spec, the next one forgets, and the wiki page changes under a run that's already going. The repo is the one place every run is guaranteed to read, at the same version. **Every question the repo doesn't answer, the agent answers with a guess.**

In a greenfield repo the specs and `AGENTS.md` are what keep parallel agent runs consistent with each other, because there's no existing code for them to agree on. If you already have a `CLAUDE.md`, that works too: our agent reads `AGENTS.md` first and falls back to `CLAUDE.md`. Ours was a one-line `CLAUDE.md` that pointed at `AGENTS.md`.

**Tests weren't there on day one.** The first check only linted and typechecked. The agent added tests in its very first PR, which means it also decided what the tests looked like. That worked out, but it's one more choice we handed over without meaning to. I'd now ship one passing test per app in the scaffold.

**Why not let the agent write the scaffold?** It's tempting: one more ticket, "set up the repo". But the scaffold *is* the set of decisions. Hand that ticket over and you've let the agent decide everything at once, which is the thing we were trying to avoid.

## What the scaffold couldn't stop

The scaffold kept the stack and the UI on rails. It didn't fix the parts that were never in the repo.

- **Design changes from outside.** The designer's Figma export landed as a restyle, and one agent PR became obsolete overnight. The design system only helps if it's where the design changes too.
- **Review was the bottleneck.** The agent opened chains of stacked PRs overnight. Some waited around 20 hours for a human, then had to be rebased onto each other by hand.
- **Infra stayed human.** Deploy, cloud resources and secrets were all done by people. The agent has no cloud access, and it shouldn't.

None of these are repo problems. They're the human side of the loop. **The scaffold keeps the agent on rails. It doesn't build the rails for the humans.**

## Before the next empty repo

We wanted a POC fast and an agent that wouldn't go wild. What got us both was not a cleverer prompt but six decisions, written down and committed before the first ticket.

> The agent will fill an empty repo either way. The scaffold decides whose choices go in.

Before you assign the first ticket, open the repo as the agent would. If you can't tell what stack to use, neither can it.

Here's the list I use now. The must-haves spell **STACKS**:

**Must have**

- [ ] **S**tack decided, with languages, package managers and versions pinned, including the UI component library if there's UI
- [ ] **T**ests: at least one passing test per app or package
- [ ] **A**GENTS.md: the stack, the commands, the allowed tools, the files the agent must not edit
- [ ] **C**ommands: one documented command to set up and one to check (lint, format, typecheck, tests). `make` is optional; one entry point that the agent and CI share is not
- [ ] **K**ickoff commit on the default branch (the agent clones it; a truly empty repo can't even start)
- [ ] **S**pecs committed to the repo, and **s**ecrets kept out of it, with settings documented in an example env file

**Strongly recommended**

- [ ] Lock files committed, and CI installing in frozen/locked mode
- [ ] CI running the check on every PR, required by branch protection
- [ ] A design system, if there's UI, with an "only these components" rule

**Later**

- [ ] A warm image, once the dependencies settle down

Before the first ticket, check your STACKS. Whatever's missing, the agent will fill in.
