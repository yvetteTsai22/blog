"""Literature-note mapping and staging (spec §1.3 step 6, §2)."""
from .mapping import format_reader_questions, parse_reader_questions, render_body, to_properties
from .outbox import Outbox
from .sink import NoteSink, OutboxSink

__all__ = ["format_reader_questions", "parse_reader_questions", "render_body", "to_properties", "Outbox", "NoteSink", "OutboxSink"]
