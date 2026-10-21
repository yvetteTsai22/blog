"""Discover per-session and nightly steps from batch/steps/*.py (see README)."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Callable

from batch import steps as steps_pkg

SESSION = "session"
NIGHTLY = "nightly"
KINDS = (SESSION, NIGHTLY)


@dataclass(frozen=True)
class Step:
    name: str
    kind: str
    order: int
    run: Callable


def _as_step(mod: ModuleType) -> Step | None:
    kind = getattr(mod, "KIND", None)
    run = getattr(mod, "run", None)
    if kind not in KINDS or not callable(run):
        return None
    return Step(
        name=getattr(mod, "NAME", None) or mod.__name__.rsplit(".", 1)[-1],
        kind=kind,
        order=int(getattr(mod, "ORDER", 100)),
        run=run,
    )


def discover(package=steps_pkg) -> dict[str, list[Step]]:
    found: dict[str, list[Step]] = {k: [] for k in KINDS}
    for info in pkgutil.iter_modules(package.__path__):
        if info.name.startswith("_"):
            continue
        step = _as_step(importlib.import_module(f"{package.__name__}.{info.name}"))
        if step:
            found[step.kind].append(step)
    for kind in KINDS:
        found[kind].sort(key=lambda s: (s.order, s.name))
    return found
