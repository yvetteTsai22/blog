"""Haiku summary + scoring via `claude -p` (spec §1.3 step 4)."""
from .parse import ParseError, Summary, parse_output
from .posts import PostOption, load_post_options
from .prompt import build_prompt

__all__ = ["ParseError", "Summary", "parse_output", "PostOption", "load_post_options", "build_prompt"]
