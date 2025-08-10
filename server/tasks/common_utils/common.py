import os
from pathlib import Path

import pendulum
import requests
import tqdm
from jinja2 import Template
from loguru import logger

from .model_types import Namelist


def check_files(expected_files, path=""):
    result = True
    if type(expected_files) is str:
        expected_files = [expected_files]
    for file in expected_files:
        if not Path(path, file).is_file():
            logger.info(f"File {file} has not been generated!")
            result = False
            break
    return result


def check_files_exist_one(files: list, all_exist: bool = True):
    """Check if files exist."""
    error_files = []
    exist_files = []
    for file in files:
        if not os.path.exists(file):
            error_files.append(file)
        else:
            exist_files.append(file)
    if all_exist:
        if error_files:
            return False, error_files
    else:
        if not exist_files:
            return False, error_files
    return True, None


def render_template(template_file: str, data: dict) -> str:
    print("rendering template ", template_file)

    with open(template_file, "r") as tf:
        template = Template(tf.read())
        return template.render(data)


def get_stilt_job_id(time: pendulum.DateTime, longitude, latitude, zagl):
    """Generate STILT job ID."""
    # /home/wrf_model/data/stilt_data/20240418/202404182100_117.1914_36.9719_2_foot.nc"""
    longitude = int(longitude) if int(longitude) == longitude else longitude
    latitude = int(latitude) if int(latitude) == latitude else latitude
    job_id = time.format("YYYYMMDDHH00") + f"_{longitude}_{latitude}_{zagl}"
    return job_id


def get_stilt_out_filename(namelist: Namelist, stilt_wd: str):
    """Get STILT output filenames."""
    file_list = []
    for hour_delta in range(int((namelist.t_end - namelist.t_start).total_hours())):
        time = namelist.t_start.add(hours=hour_delta)
        job_id = get_stilt_job_id(
            time=time, longitude=namelist.long, latitude=namelist.lati, zagl=namelist.zagl
        )
        filename = os.path.join(stilt_wd, "out", "by-id", job_id, f"{job_id}_foot.nc")
        file_list.append(filename)
    return file_list


def download_file(url: str, save_path: Path):
    """Download file from url."""
    if os.path.exists(save_path):
        logger.info(f"exist：{save_path}")
        return
    logger.info(f"start：{save_path.name}")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        total = int(r.headers.get("content-length", 0))
        with open(save_path, "wb") as f:
            with tqdm.tqdm(
                total=total, unit="B", unit_scale=True, unit_divisor=1024, desc=save_path.name
            ) as pbar:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
                    pbar.update(len(chunk))
