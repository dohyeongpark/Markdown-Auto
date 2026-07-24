from fastapi import FastAPI

from app.webhook import router as webhook_router

app = FastAPI(title="Markdown Auto")
app.include_router(webhook_router)
