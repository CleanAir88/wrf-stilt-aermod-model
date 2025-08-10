import sys

import pendulum
from celery import shared_task

sys.path.append("../../")
# from tasks.wrf_stilt_aermod_task.main import run as wrf_stilt_run
from tasks.wrf_stilt_aermod_task.main import run as wrf_stilt_run


@shared_task(name="wrf_stilt_task", bind=True)
def run_wrf_stilt_task(self, *args, **kwargs):
    if not kwargs.get("run_date"):
        scheduled_time = pendulum.now("UTC").start_of("hour").to_datetime_string()
        kwargs["run_date"] = scheduled_time
    wrf_stilt_run(*args, **kwargs)
    return "WRF-STILT task completed"
