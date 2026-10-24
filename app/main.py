"""L2 Service and L3 request logging.

L2 tasks (about 12 minutes). Run `bash grade.sh l2` to check.
1. `GET /healthz` returns {"status": "ok"}.
2. `POST /triage` takes a Complaint, calls the model with a timeout of TIMEOUT_S seconds,
   and returns parse_triage(raw). On timeout, return human_review("model timed out").
Then run it:  uvicorn app.main:app --reload --port 8000   and open the forwarded port's /docs page.

L3 tasks: see ASSIGNMENT.md.
"""

from __future__ import annotations

import asyncio  # noqa: F401  (you'll need asyncio.timeout)
import os
import time  # noqa: F401  (L3)
import uuid  # noqa: F401  (L3)

from fastapi import FastAPI, Request

from app.llm import PROMPT_VERSION, get_llm  # noqa: F401  (PROMPT_VERSION is for L3)
from app.logging_setup import logger, setup_logging  # noqa: F401  (L3)
from app.models import Complaint, TriageResult, human_review, parse_triage  # noqa: F401

TIMEOUT_S = float(os.environ.get("TRIAGE_TIMEOUT_S", "5"))
llm = get_llm()
setup_logging()
app = FastAPI(title="Example Bank complaint triage", version="0.1.0")


# TODO (L3.3): request-logging middleware. See ASSIGNMENT.md.
@app.middleware("http")
async def request_log(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:12]
    request.state.log = {}
    start = time.perf_counter()
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    logger.info(
        "request",
        extra={
            "request_id": request_id,
            "route": request.url.path,
            "status": response.status_code,
            "latency_ms": round((time.perf_counter() - start) * 1000, 1),
            **request.state.log,
        },
    )
    return response

@app.get("/healthz")
def healthz() -> dict:
    return {"status": "ok"}


@app.post("/triage", response_model=TriageResult)
async def triage(complaint: Complaint, request: Request) -> TriageResult:
    # (L2.2): the pattern (fill it in and remove the raise):
      try:
          async with asyncio.timeout(TIMEOUT_S):
              raw = await llm.complete(complaint.id, complaint.text)
          result = parse_triage(raw)
      except TimeoutError:
          result = human_review("model timed out")
      request.state.log = {
          "model": llm.model,
          "prompt_version": PROMPT_VERSION,
          "outcome": "human_review" if result.needs_human else "routed",
          "complaint_excerpt": complaint.text[:80],
      }
      return result
    
    