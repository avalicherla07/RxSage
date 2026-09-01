"""Analysis routes — POST /v1/analyze and GET /v1/analyze/{request_id}."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from api.middleware.auth import verify_api_key
from api.middleware.rate_limiter import check_rate_limit, RATE_LIMITS
from db import supabase as db
from models.request import AnalysisRequest
from models.response import AnalysisResponse, APIKeyRecord
from services import orchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/analyze", response_model=AnalysisResponse,
             summary="Run drug interaction analysis",
             description="Rate limited per API key. Returns full clinical analysis.")
async def analyze(
    body: AnalysisRequest,
    key_record: APIKeyRecord = Depends(verify_api_key),
) -> JSONResponse:
    # Run analysis first — cache hits are free, don't rate limit them
    response, _ = await orchestrator.analyze(body, key_record)

    # Only count non-cached requests against rate limit (GPT-4o costs money)
    remaining = {"remaining_minute": RATE_LIMITS["per_minute"], "remaining_hour": RATE_LIMITS["per_hour"]}
    if not response.cache_hit:
        remaining = await check_rate_limit(key_record.id)

    jr = JSONResponse(content=jsonable_encoder(response))
    jr.headers["X-RateLimit-Limit-Minute"] = str(RATE_LIMITS["per_minute"])
    jr.headers["X-RateLimit-Limit-Hour"] = str(RATE_LIMITS["per_hour"])
    jr.headers["X-RateLimit-Remaining-Minute"] = str(remaining["remaining_minute"])
    jr.headers["X-RateLimit-Remaining-Hour"] = str(remaining["remaining_hour"])
    return jr


@router.get("/analyze/{request_id}", response_model=AnalysisResponse,
            summary="Retrieve cached analysis")
async def get_cached_analysis(
    request_id: str,
    key_record: APIKeyRecord = Depends(verify_api_key),
) -> AnalysisResponse:
    cached = await db.get_cached_analysis(request_id)
    if cached is None:
        raise HTTPException(status_code=404, detail={
            "error": "Analysis not found", "code": "ANALYSIS_NOT_FOUND"})
    return cached
