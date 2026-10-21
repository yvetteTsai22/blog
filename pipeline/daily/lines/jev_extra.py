"""Global message line "Jev 另外推": Jev's top-3 topics Haiku did not list, each with its Notion link."""
from __future__ import annotations

from jev.topline import jev_top_topics, render

KIND = "global"
ORDER = 40


def lines(ctx):
    listed = {t.key for t in ctx.listed}
    return render(jev_top_topics(ctx.pool, listed))
