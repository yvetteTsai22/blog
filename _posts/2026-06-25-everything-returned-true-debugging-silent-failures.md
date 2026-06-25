---
date: 2026-06-25 08:00:00
layout: post
title: "Everything Returned True: Debugging Silent Failures in an AI Chatbot Feature"
subtitle: "Six bugs from a day shipping form-panel editing — and the pattern they share."
description: >-
  A retrospective on building a form-edit feature for an AI forecasting chatbot. Six bugs that didn't crash — they just quietly did nothing — and what they reveal about building on LLM infrastructure.
image: https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?q=80&w=2670&auto=format&fit=crop
optimized_image: >-
  https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?q=80&w=800&auto=format&fit=crop
category: code
tags:
  - python
  - debugging
  - ai
  - tutorial
author: yvetteTsai
paginate: true
---

The most dangerous bug is the one that doesn't crash.

Today I shipped a form-panel editing feature for a forecasting chatbot. Users can now edit time slots directly from the UI without typing natural language commands — the feature routes all edits through a new `/update-slots` command that reuses the same validation guards as the chat path.

What shipped: `run_slot_update()` extracted as a shared function, `UpdateSlotsCommand` with 12/12 tests green, and a WebSocket handler refactored from 218 down to 132 lines with `_handle_form_edit` deleted entirely.

At every step, bugs that didn't fail loudly. They just quietly did nothing, returned the wrong thing, or stored data in a format that looked fine until you looked closely.

Here are six of them.

--page-break--

## Bug 1: `_apply_replace` always returned `True`

`_merge_slot_entries` called `_apply_replace` to detect whether a slot value had changed. The function compared nothing. It returned `True` unconditionally.

This meant the "no changes detected" early-return in `run_slot_update` never fired — any update, even one with identical values, passed through as a real change. Tests that expected the guard to catch no-ops were passing for the wrong reason.

```python
# Before: unconditional return
def _apply_replace(slot, new_value):
    slot.value = new_value
    return True  # always "changed"

# After: compare first
def _apply_replace(slot, new_value):
    if slot.value == new_value:
        return False
    slot.value = new_value
    return True
```

A function named "apply" and a function named "detect change" are different functions. When they share a body, one of them lies.

> **Rule:** Verify the postcondition, not just the return value. Check what actually changed in the data, not what the return value claimed.

## Bug 2: `SlotEntry` can't hold what the form sends

The task brief assumed all form edits could route through `SlotEntry`. But `SlotEntry.values` is typed `str | int | float | list[str|int|float] | None`. Constraint and property values from the form panel are already in API format — they're dicts.

Pydantic rejects them. No crash in all conditions, just a silent coercion failure that surfaces downstream when the wrong shape reaches the guards.

The fix was a dual-path: a `_coerce_to_slot_entry_values()` helper that tries the `SlotEntry` path first; if it returns `None`, falls through to a direct-apply path that runs guards manually against the raw value.

> **Rule:** "Just pass it through" is never a safe assumption across a type boundary. Verify the schema on both sides before assuming one shape can traverse both.

## Bug 3: `delta` was a variable that didn't exist

The plan template referenced `delta.get("validation_errors")` in the WebSocket handler. In the actual codebase, there is no `delta` alias — the correct reference is `event.actions.state_delta`.

The template was written from memory of how the code *should* look, not how it did. Variable names don't survive translation from a planning document into a codebase.

> **Rule:** Always verify variable names by reading the actual function context. Plans drift. Code has scope.

## Bug 4: Passthrough fallbacks are where schema bugs hide

This was the hardest one. The natural-language path and the UI form path used different schemas for the same constraint data.

The NL path produces:

```json
{
  "dimensions": [{ "index": 1, "values": ["UK"] }],
  "max_spend": 1000
}
```

The UI modal was sending:

```json
{
  "dims": [{ "dimIndex": "1", "value": "UK" }],
  "min_spend": 1000
}
```

`slot_merger._decode_constraint_values` only handles s-expression strings. When it encountered a raw UI object, it passed it through unchanged — no error, no warning. So `dimIndex: "1"` got stored verbatim as a string, and "UK" appeared in the constraints panel under the wrong dimension index. Nothing crashed.

The fix was bidirectional translation in `ConstraintsEditModal.jsx`: `useEffect` to convert backend shape into UI dims on load, and `handleSave` to group by `Number(dimIndex)` and emit the backend `dimensions[]` shape. Also: explicit empty-field stripping, and `Number()` casting for React's string-returning number inputs (a trap that bites every time).

The pattern that enabled this bug: **passthrough fallbacks** — code that says "I don't recognize this format, so I'll return it unchanged." Silent passthrough is silent data corruption when the shapes don't match. The merge function saw an object it didn't understand and cooperated anyway.

> **Rule:** Passthrough is where schema bugs go to hide. Every format boundary needs an explicit translation, not a graceful shrug.

## Bug 5: The worktree needed `npm install`

`make dev` failed with `sh: vite: command not found`. The fix was `npm install`. Five seconds.

The cost wasn't the fix — it was context. I was mid-flow on a different problem when the environment broke. Isolated git worktrees don't inherit `node_modules`.

> **Rule:** Bootstrap an isolated environment before you start work, not when it fails at the worst moment.

## Bug 6: `uv run pip install` is the wrong command

In a `uv`-managed Python project, the correct command is `uv pip install`. Running `uv run pip install` wraps pip in a subprocess that doesn't write to the right environment. The install succeeds; the package doesn't appear where you expect it.

If the repo has `uv.lock` or `.python-version`, use `uv` for everything. The verbs matter.

---

## The shared pattern

Every bug here had the same structure: code that looked like it was doing the job, returned something that looked like success, and quietly failed to change anything that mattered.

`_apply_replace` returned `True`. Passthrough returned the object. Template variables resolved to the wrong name. The wrong schema stored without complaint.

When you're building on AI infrastructure — LLMs, typed ADK pipelines, multiple API shapes in the same call chain — silent no-ops are especially hard to catch. Nothing crashes. Logs look fine. The assertion just doesn't fire because the data is subtly wrong three layers up.

The fix is the same every time: verify the postcondition, not just the return value. Check the actual data after the merge. Assert the schema after the translation. Run the test that depends on the guard, not just the guard itself.

---

## What's still open

Two items carried out as known unknowns — which is better than the other kind.

The `PerformanceAdjustmentsEditModal` needs the same dual-path pattern and schema translation as the constraint modal. And the ADK command-dispatch path needs explicit OpenTelemetry `execute_tool` spans — the LLM-invoked tool path gets them automatically, but command dispatch bypasses that instrumentation entirely and is currently invisible in traces.

Naming the open work matters. A bug you've located and deferred is much less dangerous than one you don't know exists.
