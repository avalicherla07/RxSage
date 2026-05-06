"""Health check route — no authentication required."""
from __future__ import annotations

from fastapi import APIRouter

router = APIRouter()


@router.get("/v1/health")
async def health() -> dict:
    """Return {"status": "ok"} — no auth required."""
    return {"status": "ok"}
