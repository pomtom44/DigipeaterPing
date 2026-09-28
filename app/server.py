from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from . import config
from .store import PingStore

STATIC_DIR = Path(__file__).parent.parent / "static"


def create_app(store: PingStore) -> FastAPI:
    app = FastAPI(title="DigipeaterPing")

    @app.get("/")
    async def root():
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/pings")
    async def list_pings(callsign: str = "", limit: int = 50):
        limit = max(1, min(limit, 200))
        return {"callsign": config.MYCALL, "pings": store.recent(limit=limit, from_call=callsign or None)}

    return app
