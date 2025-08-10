import os
import sys
from pathlib import Path
from typing import Optional

import pendulum
import typer
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
import config
from tasks.wrf_stilt_aermod_task.crud import clean_old_wrf_files, get_model_config
from tasks.wrf_stilt_aermod_task.get_data import (
    get_gfs_data,
    get_obs_data,
    get_rda_data,
)
from tasks.wrf_stilt_aermod_task.run_aermod import run_aermod_all
from tasks.wrf_stilt_aermod_task.run_obsgrid import run_obsgrid
from tasks.wrf_stilt_aermod_task.run_process_model_config import process_all_config
from tasks.wrf_stilt_aermod_task.run_stilt import run_stilt
from tasks.wrf_stilt_aermod_task.run_wps import run_wps_geogrid, run_wps_ungrib_metgrid
from tasks.wrf_stilt_aermod_task.run_wrf import run_wrf


def run(
    run_date: str = pendulum.now("UTC").start_of("hour").to_datetime_string(),
    wrf: bool = True,
    stilt: bool = True,
    aermod: bool = True,
    receptor_ids: Optional[str] = None,
    is_delay: bool = False,
):
    """
    运行 WRF-STILT 模型
    run_date: 运行日期 格式为 YYYY-MM-DD HH:mm:ss 使用UTC时区 仅在 0 6 12 18 点执行
    data_source: 数据源 fnl / gfs
    """

    model_config = get_model_config()
    if model_config is None:
        raise Exception("No model config found.")

    obsgrid_enabled = model_config["obsgrid_enabled"]
    data_source = model_config["data_source"]
    delay_hours = model_config["data_delay_hours"]
    if not is_delay:
        delay_hours = 0

    config.START_DATE = pendulum.parse(run_date).in_tz("UTC").subtract(hours=delay_hours)
    config.END_DATE = config.START_DATE.add(hours=6)
    # wrf和stilt 只能运行在0 6 12 18点，aermod可以运行在其他时间
    if config.START_DATE.hour not in [0, 6, 12, 18] and (wrf or stilt):
        raise Exception("run_date must be 0 6 12 18 hour.")
    logger.info(
        f"run_date: {run_date}, wrf: {wrf}, obsgrid: {obsgrid_enabled}, stilt: {stilt},"
        f" data_source: {data_source}, receptor_ids: {receptor_ids}, st:"
        f" {config.START_DATE.to_datetime_string()}, et: {config.END_DATE.to_datetime_string()}"
    )
    clean_old_wrf_files(
        directory_path=Path(config.WRFOUT_DATA_PATH),
        days_threshold=model_config["wrf_file_retention_days"],
    )
    max_dom = model_config["max_dom"]
    if wrf:
        process_all_config(model_config, obsgrid=obsgrid_enabled)
        # ds083_2_fnl / gfs
        if data_source == "fnl":
            get_rda_data.run_download_ds083_2_data(model_config["fnl_url"])
        else:
            get_gfs_data.run_download_gfs_data(model_config["gfs_url"])

        if obsgrid_enabled:
            get_obs_data.run_download_obs_data(model_config)

        run_wps_geogrid(max_dom=max_dom)

        run_wps_ungrib_metgrid(
            data_source=data_source, interval_seconds=model_config["interval_seconds"]
        )
        if obsgrid_enabled:
            if model_config["obsgrid_upper_air_url"]:
                get_rda_data.run_download_ds351_data(model_config["obsgrid_upper_air_url"])
            run_obsgrid(interval_seconds=model_config["interval_seconds"], max_dom=max_dom)
        run_wrf(obsgrid=obsgrid_enabled, core_nums=model_config["n_cores"], max_dom=max_dom)

    if stilt:
        run_stilt(model_config=model_config, receptor_ids=receptor_ids)

    if aermod:
        run_aermod_all(model_config=model_config)


if __name__ == "__main__":
    typer.run(run)
