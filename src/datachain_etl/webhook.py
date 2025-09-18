"""FastAPI app that exposes a webhook for near real-time ETL."""

from __future__ import annotations

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .etl_core import ETLPipeline


class WebhookPayload(BaseModel):
    """Payload describing the file that needs to be processed."""

    ticket_id: str
    file_path: str


def create_app(pipeline: ETLPipeline) -> FastAPI:
    """Create a configured FastAPI application."""

    app = FastAPI(title="Datachain ETL Webhook")

    @app.post("/webhook")
    async def ingest(payload: WebhookPayload) -> dict[str, str]:
        try:
            output = pipeline.process_single(payload.ticket_id, payload.file_path)
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {"status": "ok", "output_path": str(output)}

    return app
