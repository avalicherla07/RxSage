"""RxSage Test Dashboard — local web UI for viewing test results.

Run: uvicorn tools.dashboard.app:app --port 8001 --reload
Open: http://localhost:8001
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import httpx
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse

# Load .env
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and k not in os.environ:
            os.environ[k] = v

app = FastAPI(title="RxSage Test Dashboard")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

API_URL = os.getenv("CLARVYN_API_URL", "http://localhost:8000").rstrip("/")
API_KEY = os.getenv("CLARVYN_API_KEY", "")


@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    html_path = Path(__file__).parent / "index.html"
    return HTMLResponse(html_path.read_text())


@app.post("/run-scenario")
async def run_scenario(payload: dict):
    """Proxy a scenario to the main RxSage API."""
    start = time.time()
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(
                f"{API_URL}/v1/analyze",
                json=payload,
                headers={"X-API-Key": API_KEY, "Content-Type": "application/json"},
            )
            elapsed_ms = int((time.time() - start) * 1000)
            return JSONResponse({
                "status_code": response.status_code,
                "elapsed_ms": elapsed_ms,
                "data": response.json(),
            })
    except httpx.ConnectError:
        return JSONResponse(
            {"error": f"Could not connect to RxSage at {API_URL}", "tip": "Start the API first"},
            status_code=503,
        )
    except Exception as exc:
        return JSONResponse({"error": str(exc)}, status_code=500)


@app.get("/health-check")
async def check_api_health():
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(f"{API_URL}/v1/health")
            return {"online": True, "status": r.json()}
    except Exception:
        return {"online": False, "url": API_URL}


@app.get("/scenarios")
async def get_scenarios():
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from scenarios import SCENARIOS
    return JSONResponse(SCENARIOS)
