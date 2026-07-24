from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api import router as api_router
from app.webhook import router as webhook_router

app = FastAPI(title="Markdown Auto")
app.include_router(webhook_router)
app.include_router(api_router)

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True, check_dir=False), name="frontend")
