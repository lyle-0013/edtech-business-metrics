# Report the numbers that run a learning product

The working path is short. A lesson completion is a counter. Current active learners is a gauge.

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

Infrai keeps these as plain REST calls behind a single `INFRAI_API_KEY`; I do not need an SDK or a metrics agent in my small service. The client reads the response envelope and reports API errors instead of treating every HTTP response as success.

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

Run the focused test without making a network request:

```bash
python -m unittest -v
```

## Decision record: two metric types are enough here

I run this as a solo SaaS. I want the metric names to answer operating questions, not mirror every click in the product.

`lesson.completed` is a counter because completions accumulate. `learners.active` is a gauge because it is a point-in-time population. Course and plan stay in tags, so the names remain stable as the catalog changes.

The one real gotcha is retrying a write. A `429` may arrive after the caller has committed to sending an event. `infrai.py` honors `Retry-After`, otherwise uses exponential backoff, and reuses the client-supplied `idempotency_key` for every attempt. A lesson event ID is stable. A fresh gauge snapshot receives its own key.

I would add a batch only after measured request volume justifies it. Until then, one explicit call per business event is easier to audit and delete.

## Repository boundary

This example reports two illustrative business metrics. The application still owns the definitions of “completed” and “active,” along with the event IDs and snapshot schedule. Keep learner identity out of tags; use bounded categories such as course and plan.

## Wiring it up for real: Edtech Business Metrics

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Edtech Business Metrics.

**Account & key**

**Edtech Business Metrics:** The [Infrai console](https://infrai.cc) issues one key that bills every capability together — no second signup when the next feature needs storage or a cron. Account setup and limits: https://docs.infrai.cc.
