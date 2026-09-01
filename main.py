"""RxSage API — FastAPI application entry point."""
from __future__ import annotations

import logging
import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.routes import analyze as analyze_router
from api.routes import health as health_router
from api.routes import keys as keys_router
from core.config import get_settings


# ---------------------------------------------------------------------------
# Lifespan (replaces deprecated @app.on_event)
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Configure logging on startup."""
    settings = get_settings()
    logging.basicConfig(level=getattr(logging, settings.log_level.upper(), logging.INFO))
    logging.getLogger(__name__).info("Clarvyn API starting up (log_level=%s)", settings.log_level)
    yield


app = FastAPI(
    title="RxSage API",
    description=(
        "Clinical decision support API for US dental professionals.\n\n"
        "RxSage analyzes patient medications, conditions, allergies, and supplements "
        "against candidate dental drugs to produce structured clinical guidance "
        "in dentist workflow order.\n\n"
        "## Authentication\n"
        "All requests require an `X-API-Key` header.\n\n"
        "## Rate limits\n"
        "10 requests/minute · 100 requests/hour · 500 requests/day\n\n"
        "## Support\n"
        "support@rxsage.com"
    ),
    version="1.0.0",
    contact={"name": "RxSage Support", "email": "support@rxsage.com"},
    license_info={"name": "Proprietary"},
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch all unhandled exceptions, log the traceback, return 500."""
    logging.getLogger(__name__).error(
        "Unhandled exception on %s %s:\n%s",
        request.method,
        request.url,
        traceback.format_exc(),
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Reformat Pydantic validation errors into the standard error schema."""
    return JSONResponse(
        status_code=422,
        content={"error": str(exc.errors()), "code": "VALIDATION_ERROR"},
    )


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(health_router.router)
app.include_router(analyze_router.router, prefix="/v1")
app.include_router(keys_router.router)


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run("main:app", host="0.0.0.0", port=settings.port, reload=False)
