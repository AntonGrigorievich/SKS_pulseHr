from __future__ import annotations

import logging
from uuid import uuid4

from fastapi import FastAPI, Request

logger = logging.getLogger(__name__)

app = FastAPI(title="PulseHR SMS Stub")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/sms")
async def send_sms(request: Request) -> dict[str, str]:
    try:
        payload = await request.json()
    except ValueError:
        payload = {}

    message_id = f"stub-{uuid4()}"
    logger.info(
        "SMS stub accepted message %s to %s from %s",
        message_id,
        payload.get("to"),
        payload.get("sender"),
    )
    return {"message_id": message_id, "status": "accepted"}
