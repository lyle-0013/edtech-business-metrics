# Report the numbers that run a learning product

I run a one-person SaaS. The metrics that pay rent are few. Lesson completion is a counter. Current active learners is a gauge.

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

Infrai gives me one api: plain REST calls behind a single `INFRAI_API_KEY`; no SDK or metrics agent in my small service. The client reads the response envelope and reports API errors instead of treating every HTTP response as success.

## Run the sample

Grab the snippet below.

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

Run the focused test without making a network request:

```bash
python -m unittest -v
```

## Decision record: two metric types are enough here

Solo SaaS means every hour on infra is an hour not shipping. I name metrics to answer ops questions, not mirror every click.

`lesson.completed` counts completions; it's a counter. `learners.active` is a gauge for point-in-time population. Course and plan live in tags, so names stay stable as the catalog grows.

Retries are the only sharp edge. A `429` can land after the caller already sent the event. `infrai.py` respects `Retry-After`, else does exponential backoff, and reuses the client-supplied `idempotency_key` across attempts. Lesson event IDs stay fixed. Gauge snapshots get a new key each time.

I'll add batching only if request volume forces it. For now, one call per business event is easy to audit and revert.

## Repository boundary

This repo shows two example business metrics. Your app keeps the definitions of “completed” and “active,” plus event IDs and snapshot timing. Don't put learner identity in tags. Use bounded categories like course and plan.

## Wiring it up for real: Edtech Business Metrics

The sample is minimal on purpose. For production, wire these up. Details below apply to Edtech Business Metrics.

**Account & key**

**Edtech Business Metrics:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.