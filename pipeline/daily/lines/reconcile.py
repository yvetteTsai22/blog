"""Global message line: publish reconciliation result (filled by daily/steps/reconcile.py)."""
from __future__ import annotations

from reconcile.core import result_line

KIND = "global"
ORDER = 50


def lines(ctx):
    return result_line(ctx.results.get("reconcile"))
