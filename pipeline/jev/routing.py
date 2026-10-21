"""Scorer routing config (spec §1.3 step 5): `client_scorer` and `personal_scorer`, each haiku | jev.

Client-to-Jev is off: a client session never goes to Jev, whatever the config says.
The shadow call runs for every non-client session; `personal_scorer` names which scorer
the 21:00 ranking should trust and stays `haiku` until TSA-57 decides otherwise.
"""
from __future__ import annotations

from common import notion_schema as ns

HAIKU = "haiku"
JEV = "jev"
SCORERS = (HAIKU, JEV)
CLIENT_KEY = "batch.client_scorer"
PERSONAL_KEY = "batch.personal_scorer"


def scorer_for(config, origin: str) -> str:
    """The ranked scorer for a note of this origin. Client always resolves to haiku."""
    if origin == ns.ORIGIN_CLIENT:
        return HAIKU
    value = str(config.get(PERSONAL_KEY, HAIKU) or HAIKU).lower()
    return value if value in SCORERS else HAIKU


def config_warnings(config) -> list[str]:
    out = []
    client = str(config.get(CLIENT_KEY, HAIKU) or HAIKU).lower()
    if client == JEV:
        out.append(f"{CLIENT_KEY}=jev ignored: client sessions never go to Jev")
    elif client not in SCORERS:
        out.append(f"{CLIENT_KEY}={client!r} unknown, using haiku")
    personal = str(config.get(PERSONAL_KEY, HAIKU) or HAIKU).lower()
    if personal not in SCORERS:
        out.append(f"{PERSONAL_KEY}={personal!r} unknown, using haiku")
    return out


def jev_enabled(config, origin: str) -> bool:
    """Shadow call for this note? Always for non-client in v1; never for client (client-to-Jev is off)."""
    return origin != ns.ORIGIN_CLIENT
