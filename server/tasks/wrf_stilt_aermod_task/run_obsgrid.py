import os
import sys

from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tasks.common_utils.common import check_files
from tasks.common_utils.shell import run


def change_grid_id(grid_id):
    f = open("namelist.oa", "r")
    lines = f.readlines()
    for i, line in enumerate(lines):
        if "grid_id" in line:
            lines[i] = f" grid_id                     = {grid_id}\n"
    f.close()
    fw = open("namelist.oa", "w")
    fw.writelines(lines)


def run_obsgrid(interval_seconds: int, max_dom: int):
    os.chdir(config.OBSGRID_PATH)
    os.makedirs(config.OBS_DATA_PATH, exist_ok=True)
    run(
        "rm -f met_em.* metoa_em.* OBS_DOMAIN* plotobs_out* qc_obs_raw* qc_obs_used*"
        " qc_obs_used_earth_relative* wrfsfdda*"
    )
    # 合并地面和高空观测数据 OBS:2025-06-29_06 OBS:2025062906
    run(
        f"cat {config.OBS_SURFACE_DATA_PATH}/OBS:{config.START_DATE.format('YYYY-MM-DD_HH')} "
        f"{config.OBS_SURFACE_DATA_PATH}/OBS:{config.END_DATE.format('YYYY-MM-DD_HH')} "
        f"{config.OBS_UPPER_DATA_PATH}/OBS:{config.START_DATE.format('YYYYMMDDHH')} "
        f"{config.OBS_UPPER_DATA_PATH}/OBS:{config.END_DATE.format('YYYYMMDDHH')} >> rda_obs"
    )
    run("util/get_rda_data.exe")
    run("rm -f rda_obs")
    run(f"mv OBS:* {config.OBS_DATA_PATH}")

    bkg_times = []
    bkg_time = config.START_DATE
    while bkg_time <= config.END_DATE:
        bkg_times.append(bkg_time)
        bkg_time = bkg_time.add(seconds=interval_seconds)
    metgrid_expected_files = [
        "met_em.d*.{}.nc".format(time.format("YYYY-MM-DD_HH:mm:ss")) for time in bkg_times
    ]
    for f in metgrid_expected_files:
        run(f"ln -sf {config.DATA_PATH}/metgrid_file/{f} ./")

    for i in range(max_dom):
        change_grid_id(grid_id=i + 1)
        run("./obsgrid.exe")

    obsgrid_expected_files = [
        "metoa_em.d01.{}.nc".format(time.format("YYYY-MM-DD_HH:mm:ss")) for time in bkg_times
    ]
    if check_files(obsgrid_expected_files):
        logger.success("-----run obsgrid success-----")
    else:
        raise Exception("obsgrid files not generate")
