# Copyright (c) 2026 Debashis Bhattacharjee. All Rights Reserved.
# Unauthorized copying, modification, or distribution is prohibited.
# https://github.com/Debashis2007

"""Developer Completions API — thin self-contained FastAPI POC."""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel, Field

from poc_core import MockLLM, TokenBucket, health_payload, AUTHOR_NAME, AUTHOR_FINGERPRINT, AUTHOR_GITHUB
from poc_core.safety import SafetyPlane
from poc_core.stores import InMemoryStore, MockVectorIndex

USE_CASE = "Developer Completions API"
app = FastAPI(title=USE_CASE)
llm = MockLLM()
store = InMemoryStore()
safety = SafetyPlane()

@app.get("/health")
def health():
    return health_payload(
        USE_CASE,
        {
            "author": AUTHOR_NAME,
            "author_github": AUTHOR_GITHUB,
            "fingerprint": AUTHOR_FINGERPRINT,
        },
    )

@app.get("/author")
def author():
    return {
        "author": AUTHOR_NAME,
        "github": AUTHOR_GITHUB,
        "fingerprint": AUTHOR_FINGERPRINT,
        "notice": "Copyright (c) 2026 Debashis Bhattacharjee. All Rights Reserved.",
    }


buckets: dict[str, TokenBucket] = {}
metering: list[dict] = []

class CompIn(BaseModel):
    prompt: str
    max_tokens: int = 24

@app.post("/v1/completions")
async def completions(body: CompIn, request: Request):
    key = request.headers.get("x-api-key", "anon")
    buckets.setdefault(key, TokenBucket(10, 1))
    if not buckets[key].allow():
        raise HTTPException(429, detail="RPM exceeded", headers={"Retry-After": "1"})
    text = await llm.complete(body.prompt, body.max_tokens)
    evt = {"api_key": key, "tokens": len(text.split()), "model": llm.model}
    metering.append(evt)
    return {"id": f"cmp_{len(metering)}", "text": text, "usage": evt}
