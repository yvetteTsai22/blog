from __future__ import annotations

from types import SimpleNamespace

from daily import discovery, message
from daily.lines import resume_drafting


class _Config:
    def __init__(self, local):
        self.local = local

    def get(self, dotted, default=None):
        node = self.local
        for part in dotted.split("."):
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return node


def _ctx(local):
    return SimpleNamespace(config=_Config(local))


def test_default_drafting_dir():
    assert resume_drafting.lines(_ctx({})) == [
        "接續寫作：cd ~/orca/workspaces/blog/draft-blog && claude --continue  (或 blog-write)"
    ]


def test_configured_drafting_dir():
    out = resume_drafting.lines(_ctx({"daily": {"drafting_dir": "~/w/drafts"}}))
    assert out == ["接續寫作：cd ~/w/drafts && claude --continue  (或 blog-write)"]


def test_discovered_as_last_global_provider():
    globals_ = discovery.discover_lines()["global"]
    assert globals_[-1].name == "resume_drafting"
    assert all(p.order < resume_drafting.ORDER for p in globals_[:-1])


def test_rendered_as_last_line_without_reminders():
    ctx = _ctx({})
    text = message.render("hdr", [], [], [], [], global_providers=[lambda: resume_drafting.lines(ctx)])
    assert text.rstrip("\n").splitlines()[-1].startswith("接續寫作：cd ")
