"""Report the few numbers I use to operate a small learning product."""

from dataclasses import dataclass
from uuid import uuid4

from infrai import MetricsClient, client_from_env


@dataclass(frozen=True)
class LessonSnapshot:
    course: str
    plan: str
    active_learners: int


def report_lesson_completed(
    infrai: MetricsClient, *, course: str, plan: str, event_id: str
) -> dict:
    return infrai.metrics.report(
        type="counter",
        name="lesson.completed",
        value=1,
        tags={"course": course, "plan": plan},
        idempotency_key=event_id,
    )


def report_active_learners(infrai: MetricsClient, snapshot: LessonSnapshot) -> dict:
    return infrai.metrics.report(
        type="gauge",
        name="learners.active",
        value=snapshot.active_learners,
        tags={"course": snapshot.course, "plan": snapshot.plan},
        idempotency_key=f"active-learners-{uuid4()}",
    )


def main() -> None:
    infrai = client_from_env()
    completion = report_lesson_completed(
        infrai, course="python-basics", plan="starter", event_id=str(uuid4())
    )
    active = report_active_learners(
        infrai,
        LessonSnapshot(course="python-basics", plan="starter", active_learners=42),
    )
    print({"completion": completion, "active_learners": active})


if __name__ == "__main__":
    main()
