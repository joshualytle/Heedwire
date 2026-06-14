"""Read-only local API (the feeder/consumer seam). Binds localhost by default;
auth is a documented step for exposure/multi-user, not a v1 default."""
from __future__ import annotations

from datetime import datetime

from fastapi import FastAPI

from .config import Config
from .store import Store


def create_app(cfg: Config) -> FastAPI:
    app = FastAPI(title="Heedwire", version="0.1.0")

    @app.get("/healthz")
    def healthz():
        store = Store(cfg.store_path)
        try:
            return {"ok": True, "last_run": store.get_meta("last_run")}
        finally:
            store.close()

    @app.get("/findings")
    def findings(since: str | None = None, limit: int = 200):
        store = Store(cfg.store_path)
        try:
            dt = datetime.fromisoformat(since) if since else None
            return {"items": store.recent(since=dt, limit=limit)}
        finally:
            store.close()

    @app.get("/sources")
    def sources():
        return {"sources": list(cfg.sources.keys())}

    return app
