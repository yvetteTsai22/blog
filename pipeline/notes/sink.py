"""NoteSink: where a finished record goes. v1 stages to the outbox for the MCP agent pass;
a REST sink can implement the same protocol later."""
from __future__ import annotations

from typing import Mapping, Protocol

from .outbox import Outbox


class NoteSink(Protocol):
    def write(self, record: Mapping) -> str:
        """Persist one literature note; return a reference (path or page id)."""


class OutboxSink:
    def __init__(self, outbox: Outbox):
        self.outbox = outbox

    def write(self, record: Mapping) -> str:
        return str(self.outbox.stage(record))
