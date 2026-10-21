"""Synthetic transcript builder. All content is invented; no real session data."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

T0 = datetime(2026, 1, 1, 9, 0, tzinfo=timezone.utc)


class Transcript:
    def __init__(self):
        self.lines: list[dict] = []
        self.t = T0
        self.n = 0

    def _ts(self, advance_s: float) -> str:
        self.t += timedelta(seconds=advance_s)
        return self.t.isoformat().replace("+00:00", "Z")

    def title(self, text):
        self.lines.append({"type": "ai-title", "aiTitle": text})
        return self

    def user(self, text, gap=10, meta=False):
        self.lines.append({"type": "user", "isMeta": meta, "timestamp": self._ts(gap),
                           "message": {"role": "user", "content": text}})
        return self

    def say(self, text, gap=10):
        self.lines.append({"type": "assistant", "timestamp": self._ts(gap),
                           "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}})
        return self

    def tool(self, name, inp, result="ok", error=False, gap=10):
        self.n += 1
        tid = f"toolu_{self.n}"
        self.lines.append({"type": "assistant", "timestamp": self._ts(gap),
                           "message": {"content": [{"type": "tool_use", "id": tid, "name": name, "input": inp}]}})
        self.lines.append({"type": "user", "timestamp": self._ts(1),
                           "message": {"content": [{"type": "tool_result", "tool_use_id": tid,
                                                    "content": result, "is_error": error}]}})
        return self

    def write(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join(json.dumps(x) for x in self.lines) + "\nnot json\n", encoding="utf-8")
        return path


@pytest.fixture
def tx():
    return Transcript()


@pytest.fixture
def proj(tmp_path):
    return tmp_path / "projects" / "-tmp-demo-project"
