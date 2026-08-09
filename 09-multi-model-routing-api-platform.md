# 09 — Multi-Model Routing / API Platform

**Prompt:** Design a developer API platform that routes across many models/versions with quotas, canaries, cost-aware routing, and enterprise SLAs.

**Rank:** Top 10 (#09)

## Use cases

| Use case | Who | Why this design matters |
|----------|-----|-------------------------|
| Public multi-model API | External developers | Aliases, pins, quotas, accurate billing |
| Cost-aware auto-routing | Apps optimizing $ / quality | Small→large cascade with transparency |
| Enterprise pinned deployments | B2B with change control | No surprise `latest` flips |
| Internal model gateway | Many product teams, one gate | Shared auth, metering, safety plane |
| Batch + realtime mixed API | Async jobs + interactive | Priority queues; separate capacity pools |

---

## 1. Clarify requirements

### Functional
- Standard HTTP API: chat, completions, embeddings, tools.
- Multiple models; aliases (`latest`, pinned versions).
- API keys, orgs, projects, spend limits.
- Streaming + non-streaming; batch endpoints optional.
- Usage metering & billing export.

### Non-functional
| Metric | Target |
|--------|--------|
| Gateway P99 overhead | ≤ 20–40 ms excluding model |
| Availability | 99.9%+ with regional failover |
| Metering accuracy | Exact enough to bill; reconcile daily |
| Abuse resistance | Key theft, carding, scrape storms |

### Scale axes
- RPS, token throughput, key count, model count, regions.

### Unacceptable failures
- Billing undercount at scale
- Routing to deprecated/wrong model silently
- One noisy key melting a model pool
- Cross-org data exposure via logs/cache

---

## 2. High-level architecture

```
Client → Edge → API Gateway (authn, authz, schema)
              → Quota / Rate Limiter
              → Router (model alias → revision → pool)
              → Inference fleets (per model)
              → Metering pipeline (at-least-once → exact reconcile)
              → Developer console & billing
```

---

## 3. Deep dive: routing & aliases

### Alias resolution
```
gpt-x-latest → pin map → revision r2026-04-01 → canary 5% r2026-04-15
customer pin → exact revision (no surprise)
```

- Enterprise customers often **pin**; consumers accept `latest`.
- Canary by hash(org_id) or hash(request_id) for stickiness within session.

### Cost-aware / quality-aware routing
| Strategy | When |
|----------|------|
| Static model id | Developer chose explicitly |
| Auto router | Classify prompt → small vs large model |
| Distillation cascade | Try small; escalate on low confidence |
| Region steer | Data residency / latency |

Be transparent: auto-routing must be documented; some API users require determinism.

---

## 4. Quotas & fairness

- **Dimensions:** RPM, TPM (tokens/min), concurrent requests, $ budget.
- **Algorithm:** token bucket at edge + distributed counters (Redis/Cell).
- **Hierarchy:** user ≤ project ≤ org ≤ model-pool capacity.
- Return `429` with `Retry-After` and rate limit headers.

**Priority:** paying tiers get reserved capacity; free tier shed first under overload.

---

## 5. Metering & billing

1. Emit usage events: `org`, `model_revision`, tokens in/out, cached tokens, tool fees.
2. At-least-once into stream; **idempotent aggregate** by `request_id`.
3. Hot counters for dashboards; cold warehouse for invoices.
4. Daily reconcile: gateway accepts vs inference completes (catch mismatches).

Principal line: *Meter from a single authoritative completion signal, not from optimistic accept.*

---

## 6. Reliability patterns

- Timeouts & budgets per hop.
- Hedging only for idempotent non-stream (careful with double cost).
- Regional failover with residency constraints.
- Model pool circuit breakers; fallback only if product policy allows (and mark in response headers).

---

## 7. Developer experience & safety

- Schema validation; clear error taxonomy.
- Prompt/response logging opt-in for ZDR (zero data retention) customers—default enterprise controls.
- Same safety plane as consumer, with API-specific policy (e.g. stricter on certain endpoints).
- Versioned deprecation policy with long pin windows.

---

## 8. Scale 10× / 100× / 1000×

| Scale | Breakage | Fix |
|-------|----------|-----|
| 10× RPS | Central Redis limiter | Sharded / local + global asymptotic limits |
| 100× keys | Auth lookup | Key cache; hierarchical org config |
| 1000× models | Ops chaos | Fleet templates; registry-driven deploy |

---

## 9. Multi-year bet

**Bet:** A **model registry + capacity plane** where aliases, canaries, quotas, and metering schemas are data-driven. Push policy to the edge for RPM/TPM; keep revision routing central but simple. Exact billing reconcile is a product requirement from day one.

---

## 10. 60-second summary

Authenticate and quota at the edge, resolve aliases to pinned revisions with canaries, route to isolated fleets with circuit breakers, and meter usage idempotently for billing—while keeping enterprise pins and data-retention promises sacred.
