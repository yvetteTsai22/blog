"""Nightly market signals (spec §1.3 step 8, §4). Logic lives in `market/`; see market/README.md."""
from __future__ import annotations

NAME = "market_signals"
KIND = "nightly"
ORDER = 80


def run(ctx, status):
    from market import config as market_config
    from market.pipeline import Inputs, run_nightly

    status["market"] = run_nightly(Inputs(
        state_dir=ctx.state_dir,
        cfg=market_config.load(),
        now=ctx.now,
        cycle=ctx.cycle,
        projects_dir=ctx.projects_dir,
        client_projects=tuple(ctx.client_projects),
        env_path=ctx.config.env_path,
        log=ctx.log,
    ))
