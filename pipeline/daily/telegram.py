"""Send one message via the Telegram Bot API (token + chat id from pipeline.local.yml)."""
from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from common.config import Config

MAX_LEN = 4096
TIMEOUT = 30


class TelegramError(Exception):
    """Send failed; the message never contains the token."""


def chunks(text: str, limit: int = MAX_LEN) -> list[str]:
    """Split on line boundaries so each part fits Telegram's limit."""
    parts, current = [], ""
    for line in text.splitlines(keepends=True):
        while len(line) > limit:
            if current:
                parts.append(current)
                current = ""
            parts.append(line[:limit])
            line = line[limit:]
        if len(current) + len(line) > limit:
            parts.append(current)
            current = ""
        current += line
    if current:
        parts.append(current)
    return parts


def send(config: Config, text: str) -> list[int]:
    token = config.get("telegram.bot_token")
    chat_id = config.get("telegram.chat_id")
    if not token or not chat_id:
        raise TelegramError("telegram.bot_token / telegram.chat_id missing from pipeline.local.yml")
    ids = []
    for part in chunks(text):
        data = urllib.parse.urlencode(
            {"chat_id": chat_id, "text": part, "disable_web_page_preview": "true"}
        ).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{token}/sendMessage", data=data)
        try:
            with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
                body = json.load(resp)
        except urllib.error.HTTPError as exc:
            raise TelegramError(f"sendMessage -> HTTP {exc.code}") from None
        except (urllib.error.URLError, TimeoutError) as exc:
            raise TelegramError(f"sendMessage -> {exc.__class__.__name__}") from None
        if not body.get("ok"):
            raise TelegramError("sendMessage -> ok=false")
        ids.append(body["result"]["message_id"])
    return ids
