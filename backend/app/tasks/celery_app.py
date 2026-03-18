from celery import Celery

from app.config import settings

celery_app = Celery(
    "cereborate",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.linking_tasks",
        "app.tasks.dependency_tasks",
        "app.tasks.consistency_tasks",
        "app.tasks.notification_tasks",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    # Beat schedule for periodic tasks
    beat_schedule={
        "nightly-consistency-sweep": {
            "task": "app.tasks.consistency_tasks.nightly_consistency_sweep",
            "schedule": 86400.0,  # 24 hours
        },
        "hourly-link-detection": {
            "task": "app.tasks.linking_tasks.scan_unlinked_ideas",
            "schedule": 3600.0,  # 1 hour
        },
    },
)
