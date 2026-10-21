"""Discover extra 21:00 steps (daily/steps/) and message line providers (daily/lines/). See README."""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from types import ModuleType
from typing import Callable

from daily import lines as lines_pkg
from daily import steps as steps_pkg

GLOBAL = "global"
TOPIC = "topic"
LINE_KINDS = (GLOBAL, TOPIC)


@dataclass(frozen=True)
class Plugin:
    name: str
    kind: str
    order: int
    fn: Callable


def _modules(package) -> list[ModuleType]:
    return [
        importlib.import_module(f"{package.__name__}.{info.name}")
        for info in pkgutil.iter_modules(package.__path__)
        if not info.name.startswith("_")
    ]


def _plugin(mod: ModuleType, kind: str, attr: str) -> Plugin | None:
    fn = getattr(mod, attr, None)
    if not callable(fn):
        return None
    return Plugin(
        name=getattr(mod, "NAME", None) or mod.__name__.rsplit(".", 1)[-1],
        kind=kind,
        order=int(getattr(mod, "ORDER", 100)),
        fn=fn,
    )


def _sorted(items):
    return sorted((p for p in items if p), key=lambda p: (p.order, p.name))


def discover_steps(package=steps_pkg) -> list[Plugin]:
    return _sorted(_plugin(m, "step", "run") for m in _modules(package))


def discover_lines(package=lines_pkg) -> dict[str, list[Plugin]]:
    found = {k: [] for k in LINE_KINDS}
    for mod in _modules(package):
        kind = getattr(mod, "KIND", None)
        if kind in LINE_KINDS:
            found[kind].append(_plugin(mod, kind, "lines"))
    return {k: _sorted(v) for k, v in found.items()}
