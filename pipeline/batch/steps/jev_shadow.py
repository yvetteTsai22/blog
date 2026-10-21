"""Per-session Jev shadow scoring (spec §1.3 step 5). Non-client notes only; stored, never ranked."""
from __future__ import annotations

from jev import JevClient, jev_enabled, score_sample
from jev.routing import config_warnings
from sampler import build_sample, enforce_cap, render
from summarize import load_post_options

NAME = "jev_shadow"
KIND = "session"
ORDER = 50

# Overridable in tests; built lazily so a missing key only fails this step.
client_factory = JevClient.from_config


def run(ctx, session, record):
    for warning in config_warnings(ctx.config):
        ctx.log(f"jev: {warning}")
    if not jev_enabled(ctx.config, record["origin"]):
        return None
    sample = render(session, enforce_cap(build_sample(session)))  # raw sample, never the summary
    posts = load_post_options(ctx.posts_dir) if ctx.posts_dir.is_dir() else []
    result = score_sample(client_factory(ctx.config), sample, posts)
    ctx.log(f"jev: scored {record['session_id']} ({result.model}, {result.input_tokens} tok)")
    return {
        **record,
        "extra_properties": {**record["extra_properties"], **result.properties()},
        "extra_body": [*record["extra_body"], result.body_section()],
    }
