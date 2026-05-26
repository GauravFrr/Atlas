"""
Agent-Earns premium dashboard — multi-page SPA + JSON API.
"""

from __future__ import annotations

import secrets
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.staticfiles import StaticFiles

from config import get_settings
from dashboard.api import router as api_router
from database.connection import init_db

security = HTTPBasic()
STATIC = Path(__file__).parent / "static"


def _verify(credentials: HTTPBasicCredentials) -> None:
    settings = get_settings()
    ok_user = secrets.compare_digest(credentials.username, "admin")
    ok_pass = secrets.compare_digest(
        credentials.password, settings.dashboard_password
    )
    if not (ok_user and ok_pass):
        raise HTTPException(
            status_code=401,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )


def auth(credentials: HTTPBasicCredentials = Depends(security)) -> None:
    _verify(credentials)


def create_app() -> FastAPI:
    app = FastAPI(title="Agent-Earns", docs_url=None, redoc_url=None)

    @app.on_event("startup")
    async def _startup() -> None:
        await init_db()
        STATIC.mkdir(parents=True, exist_ok=True)

    app.include_router(api_router, dependencies=[Depends(auth)])

    if STATIC.is_dir():
        app.mount("/assets", StaticFiles(directory=str(STATIC)), name="assets")

    @app.get("/")
    async def index(_: None = Depends(auth)) -> FileResponse:
        index_path = STATIC / "index.html"
        if not index_path.is_file():
            raise HTTPException(500, "Dashboard UI missing — rebuild static/")
        return FileResponse(index_path)

    return app
