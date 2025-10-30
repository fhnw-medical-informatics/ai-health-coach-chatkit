"""Exposes a ChatKit server as well as a REST API for medication management."""

from __future__ import annotations

from typing import Any

from chatkit.server import StreamingResult
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import Response, StreamingResponse
from starlette.responses import JSONResponse

from .chat import (
    HealthCoachServer,
    create_chatkit_server,
)
from .medications import medication_store

app = FastAPI(title="AI Health Coach API")

_chatkit_server: HealthCoachServer | None = create_chatkit_server()


def get_chatkit_server() -> HealthCoachServer:
    if _chatkit_server is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "ChatKit dependencies are missing. Install the ChatKit Python "
                "package to enable the conversational endpoint."
            ),
        )
    return _chatkit_server


@app.post("/chatkit")
async def chatkit_endpoint(
    request: Request, server: HealthCoachServer = Depends(get_chatkit_server)
) -> Response:
    payload = await request.body()
    result = await server.process(payload, {"request": request})
    if isinstance(result, StreamingResult):
        return StreamingResponse(result, media_type="text/event-stream")
    if hasattr(result, "json"):
        return Response(content=result.json, media_type="application/json")
    return JSONResponse(result)


@app.get("/medications")
async def list_medications() -> dict[str, Any]:
    medications = await medication_store.list_all()
    return {"medications": [medication.as_dict() for medication in medications]}


@app.delete("/medications/{medication_name}")
async def delete_medication(medication_name: str) -> dict[str, Any]:
    deleted = await medication_store.delete(medication_name)
    if not deleted:
        raise HTTPException(status_code=404, detail="Medication not found")
    
    return {"message": "Medication deleted successfully"}


@app.delete("/medications")
async def clear_all_medications() -> dict[str, Any]:
    count = await medication_store.clear_all()
    return {"message": f"Cleared {count} medications successfully"}


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}
