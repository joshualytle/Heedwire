"""Heartbeat (dead-man's-switch) tests. No network — the session is faked.

The heartbeat pings a push URL on each completed run so a *silent* failure
(crashed scheduler, dead host) is noticed by an external monitor; on errors it
pings the `/fail` path (the healthchecks.io / Uptime Kuma convention).
"""
from __future__ import annotations

import pytest

from heedwire import engine
from heedwire.config import Config
from heedwire.engine import RunResult, _heartbeat

ENV = "HEEDWIRE_HEARTBEAT_URL"


class _Session:
    def __init__(self, boom: bool = False) -> None:
        self.urls: list[str] = []
        self.boom = boom

    def get(self, url, timeout=None):
        self.urls.append(url)
        if self.boom:
            raise RuntimeError("network down")


@pytest.fixture
def fake_session(monkeypatch):
    s = _Session()
    monkeypatch.setattr(engine, "session", lambda: s)
    return s


def test_no_env_no_ping(monkeypatch, fake_session):
    monkeypatch.delenv(ENV, raising=False)
    _heartbeat(Config(), RunResult())
    assert fake_session.urls == []


def test_success_pings_base_url(monkeypatch, fake_session):
    monkeypatch.setenv(ENV, "https://hc.example/ping/abc/")
    _heartbeat(Config(), RunResult(fetched=5))
    assert fake_session.urls == ["https://hc.example/ping/abc"]


def test_errors_ping_fail_path(monkeypatch, fake_session):
    monkeypatch.setenv(ENV, "https://hc.example/ping/abc")
    _heartbeat(Config(), RunResult(errors=["kev: boom"]))
    assert fake_session.urls == ["https://hc.example/ping/abc/fail"]


def test_heartbeat_never_raises(monkeypatch):
    monkeypatch.setenv(ENV, "https://hc.example/ping/abc")
    monkeypatch.setattr(engine, "session", lambda: _Session(boom=True))
    _heartbeat(Config(), RunResult())  # must not raise
