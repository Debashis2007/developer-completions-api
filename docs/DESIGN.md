# Design: Developer Completions API

**Project:** `developer-completions-api`  
**Parent system design:** `01-llm-inference-serving.md / 09-multi-model-routing-api-platform.md`

## 1. What this POC demonstrates

Key-authenticated completions API with hard rate limits and usage metering events.

## 2. Architecture (POC)

```text
Client + x-api-key → RPM bucket → MockLLM → metering log → response
```

## 3. Patterns used (and why)

| Pattern | Why used | Where in code |
|---------|----------|---------------|
| API key isolation | Noisy neighbors are limited per key, not globally. | Per-key `TokenBucket`. |
| Usage metering event | Billing needs an authoritative completion signal. | Append-only `metering` list. |
| 429 + Retry-After | Clients can back off correctly. | `HTTPException(429)`. |

## 4. Key endpoints

`GET /health`, `POST /v1/completions`

## 5. Tradeoffs / POC limits

Metering is in-process only; a real system would emit to a durable stream and reconcile.

## 6. How to run

See the **Run (self-contained POC)** section in [`../README.md`](../README.md).

This folder is self-contained and can be published as its own GitHub repository.

## 7. Design walkthrough video

Narrated with **ElevenLabs Debpro voice** and Debpro still image (via [GitaProject](/Users/deb/Development/GenAI/GitaProject)):

- Video: [`video/design-overview.mp4`](./video/design-overview.mp4)
- Script: [`video/narration.txt`](./video/narration.txt)

