---
layout: page
title: About
description: I help teams take AI agents from demo to production — and teach engineers to do it themselves.
permalink: /about/
---

<img class="img-rounded" src="{{ '/assets/img/uploads/profile.JPG' | prepend: site.baseurl }}" alt="Yvette Tsai" width="200">

# I help teams take AI agents from demo to production — and teach engineers to do it themselves.

👋 Hi, I'm YY (Yvette Tsai), a senior AI engineer at an AI consultancy in London, with 8 years in AI. I build LLM features and agent workflows that have to work on a Tuesday afternoon, not just in a demo.

## 🛠️ Problems I've solved

- ⚡ **A multi-agent code review was too slow.** I measured 114 runs, found the real bottleneck (model turns, not tools), and learned where parallelism stops paying off. [Read the breakdown →]({{ site.baseurl }}{% post_url 2026-09-29-the-slowest-reviewer-making-a-multi-agent-code-review-faster %})
- 🐛 **An AI feature "worked" but did nothing.** Six bugs that returned `true` and quietly failed, and the pattern they share. [Read the retro →]({{ site.baseurl }}{% post_url 2026-06-25-everything-returned-true-debugging-silent-failures %})
- 🔍 **Nobody could see what the LLM was doing.** A hands-on guide to manual tracing with Google ADK. [Read the guide →]({{ '/level-up-your-llm-observability-a-hands-on-guide-to-manual-instrumentation-with-google-adk/' | prepend: site.baseurl }})

## 🤝 How I can help

### 🚀 For engineering teams: agent workflow tuning

**You:** your team uses Claude Code, Cursor, or custom agents, and they're slow, expensive, or inconsistent.

**What I do:** measure where the time and tokens actually go, then fix the workflow: split or merge agents, pick the right model for each step, and work within rate limits.

**You get:** faster runs, lower cost, and numbers that show the difference.

### 🎓 For engineers: learn to build AI that ships

**You:** you can write code, but you're not sure how to turn an LLM prototype into something reliable.

**What I do:** 1:1 mentoring on agent design, observability, and debugging the failures that don't crash.

**You get:** a working approach you can reuse on your own projects.

## 📍 Background

- Senior AI engineer at a London AI consultancy
- 8 years in AI, now focused on LLM features and agent systems
- Daily tools: Python, Claude Code, Google ADK, LLM tracing and evals
- I write here about what broke, what I measured, and what I'd do differently

## 💬 Let's talk

Have an agent workflow that needs to be faster, or want to level up as an AI builder?
[Get in touch]({{ '/contact/' | prepend: site.baseurl }}) or email [tsaimc2@gmail.com](mailto:tsaimc2@gmail.com).
