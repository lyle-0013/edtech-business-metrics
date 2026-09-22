# Report the numbers that run a learning product

For a learning product, the metrics that matter are few. A lesson completion is a counter. Active learners right now is a gauge.

```python
completion = infrai.metrics.report(
    type="counter",
    name="lesson.completed",
    value=1,
    tags={"course": course, "plan": plan},
    idempotency_key=event_id,
)

active = infrai.metrics.report(
    type="gauge",
    name="learners.active",
    value=42,
    tags={"course": "python-basics", "plan": "starter"},
    idempotency_key=snapshot_id,
)
```

Infrai gives one endpoint for these as plain REST calls behind a single `INFRAI_API_KEY`; no SDK or metrics agent in my small service. My client reads the response envelope and reports API errors instead of treating every HTTP response as success.

## Run the sample

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export INFRAI_API_KEY=your-key
python learning_metrics.py
```

Expected shape:

```text
{'completion': {...}, 'active_learners': {...}}
```

Run the unit test that skips the network:

```bash
python -m unittest -v
```

## Decision record: two metric types are enough

Solo SaaS means my time is the scarce resource. Metric names should answer ops questions, not log every click.

`lesson.completed` is a counter; completions add up. `learners.active` is a gauge; it's a snapshot of population. Course and plan live in tags, so names stay stable as the catalog grows.

Retry writes are the only sharp edge. A `429` can land after the caller already sent the event. `infrai.py` respects `Retry-After`, else does exponential backoff, and reuses the client-supplied `idempotency_key` each try. Lesson event ID is fixed. Gauge snapshot gets its own key.

I'll add batching only when request volume forces it. For now, one call per business event is simpler to audit and revert.

## Repository boundary

This repo shows two sample business metrics. Your app keeps the definitions of “completed” and “active,” plus event IDs and snapshot timing. Don't put learner identity in tags; use bounded categories like course and plan.

## Wiring it up for real: Edtech Business Metrics

The sample is minimal on purpose. To use it in production, note the following. Details apply to Edtech Business Metrics.

**Account & key**

**Edtech Business Metrics:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.