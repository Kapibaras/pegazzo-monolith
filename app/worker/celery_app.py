from celery import Celery
from kombu import Queue

from app.config import CELERY

app = Celery("pegazzo")

app.conf.update(
    broker_url=CELERY.BROKER_URL,
    result_backend=CELERY.RESULT_BACKEND,
    accept_content=["json"],
    task_serializer="json",
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=240,
    task_time_limit=300,
    task_always_eager=CELERY.TASK_ALWAYS_EAGER,
    task_eager_propagates=True,
    task_default_queue="documents",
    task_queues=[
        Queue("documents", routing_key="documents"),
    ],
)

app.conf.include = [
    "app.worker.tasks.dummy",
    "app.worker.beat_schedules",
]
