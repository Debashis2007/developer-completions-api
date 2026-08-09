# Use Case: Developer Completions / Chat API

**YouTube walkthrough:** [Developer Completions Api — System Design #Shorts](https://youtu.be/od1oVlLfn1A)

**Design doc:** [docs/DESIGN.md](./docs/DESIGN.md) — architecture, patterns, and why.


**Parent system design:** [01 — LLM Inference Serving](../01-llm-inference-serving.md)  
**Also references:** [09 — Multi-model routing / API platform](../09-multi-model-routing-api-platform.md)

## Users & problem

Third-party developers call a completions/chat API with API keys. They need predictable latency, hard rate limits, accurate usage metering, and isolation from noisy neighbors.

## Requirements & SLOs

| Requirement | Target |
|-------------|--------|
| TTFT P99 | ≤ 300 ms (paid tiers) |
| Rate limits | RPM + TPM per key/org |
| Metering | Billable token accuracy with daily reconcile |
| Isolation | No cross-org cache/prompt leakage |
| Versions | Pinable model revisions |

## Design (from parent)

```
API key → Gateway (auth, schema) → Quota (RPM/TPM)
        → Router (alias → revision → pool)
        → Inference workers (continuous batching)
        → Metering event → billing
```

Reuse from **01**: worker fleet, KV/batching, admission control.  
Reuse from **09**: aliases, quotas, metering, deprecation policy.

## Specializations

| Concern | Design choice |
|---------|---------------|
| Fairness | Hard 429s with `Retry-After`; reserved capacity for paid |
| Caching | Prefix cache keyed by org (never cross-org) |
| Streaming | Optional SSE; same generation_id resume as [02](../02-streaming-token-delivery.md) |
| Abuse | Spend caps, anomaly detection ([05](../05-model-monitoring-observability.md)) |

## Failure modes

- One key floods TPM → org-level circuit breaker, not fleet-wide meltdown.
- Metering lag → accept path must still emit idempotent `request_id` usage.
- Wrong revision routed → alias map + canary sticky by org hash.




## Design walkthrough (opens on GitHub)

> **Watch on YouTube:** [Developer Completions Api — System Design #Shorts](https://youtu.be/od1oVlLfn1A)


![Design overview](docs/video/design-overview.gif)

Full narrated video (download): [docs/video/design-overview.mp4](docs/video/design-overview.mp4)

## Run (self-contained POC)

This folder is a **standalone** project (safe to split into its own GitHub repo).

```bash
cd developer-completions-api
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
PYTHONPATH=. python -m uvicorn app.main:app --reload --port 8000
```

```bash
curl -s http://127.0.0.1:8000/health | jq
```

curl -s -X POST http://127.0.0.1:8000/v1/completions -H 'x-api-key: demo' -H 'Content-Type: application/json' -d '{"prompt":"hello"}' | jq
