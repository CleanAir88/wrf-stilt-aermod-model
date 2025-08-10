import os

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "server.settings")

app = Celery("air_tracker_celery")
app.config_from_object("django.conf:settings", namespace="CELERY")


app.conf.update(
    worker_name="wrf_stilt_worker",
    broker_url="redis://127.0.0.1:6379/0",
    result_expires=3600 * 24 * 30,  # 30天
    worker_concurrency=1,
    beat_scheduler="django_celery_beat.schedulers:DatabaseScheduler",
    result_backend="django-db",
    result_extended=True,
    cache_backend="django-cache",
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    enable_utc=True,
    broker_connection_retry_on_startup=True,
    task_default_queue="default",
    task_default_routing_key="default",
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("wrf_stilt", Exchange("wrf_stilt"), routing_key="wrf_stilt"),
    ),
    task_routes={
        "wrf_stilt_task": {
            "queue": "wrf_stilt",
            "routing_key": "wrf_stilt",
        },
    },
)

# cron job
app.conf.beat_schedule = {
    "wrf_stilt_task": {
        "task": "wrf_stilt_task",
        "schedule": crontab(minute=0, hour="0,6,12,18"),  # utc 22,4,10,16
        "kwargs": {
            "is_delay": True,
        },
    },
}

app.autodiscover_tasks(["apps.model_wrf_stilt.tasks"])
