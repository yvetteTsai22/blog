"""Keep batch tests hermetic: no real steps, no network.

Without this, `stage_queue` auto-discovers batch/steps/ and runs Jev scoring
(real API calls), market signals (GitHub/Reddit/... fetches) and the fastembed
model load — minutes per test. Tests that want steps patch `batch.runner.discover`
themselves; that later setattr wins over this default.
"""
import socket

import pytest


@pytest.fixture(autouse=True)
def no_real_steps(monkeypatch):
    monkeypatch.setattr("batch.runner.discover", lambda: {"session": [], "nightly": []})


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    real_connect = socket.socket.connect

    def guarded(sock, address):
        if sock.family == socket.AF_UNIX:
            return real_connect(sock, address)
        raise RuntimeError(f"batch tests must not touch the network (connect to {address!r})")

    monkeypatch.setattr(socket.socket, "connect", guarded)
