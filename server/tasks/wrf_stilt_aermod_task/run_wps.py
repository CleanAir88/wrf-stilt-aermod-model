import os
import sys

from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tasks.common_utils.common import check_files
from tasks.common_utils.shell import run
from tasks.wrf_stilt_aermod_task.get_data import get_gfs_data, get_rda_data


def run_wps_geogrid(max_dom: int):
    os.chdir(config.WPS_PATH)
    logger.info(f"Run geogrid.exe at {config.WPS_PATH} ...")
    expected_files = ["geo_em.d{:02d}.nc".format(i + 1) for i in range(max_dom)]
    if check_files(expected_files):
        logger.success("-----geogrid files already exist-----")
        return

    run("rm -f geo_em.d*.nc")
    run("./geogrid.exe")

    if check_files(expected_files):
        logger.success("-----run geogrid success-----")
    else:
        raise Exception("geogrid.exe failed!")


def run_wps_ungrib_metgrid(data_source: str, interval_seconds: int):
    os.chdir(config.WPS_PATH)

    os.makedirs(config.UNGRIB_PATH, exist_ok=True)
    os.makedirs(config.METGRID_PATH, exist_ok=True)

    bkg_times = []
    bkg_time = config.START_DATE
    while bkg_time <= config.END_DATE:
        bkg_times.append(bkg_time)
        bkg_time = bkg_time.add(seconds=interval_seconds)
    ungrib_expected_files = [f'FILE:{time.format("YYYY-MM-DD_HH")}' for time in bkg_times]
    metgrid_expected_files = [
        "met_em.d01.{}.nc".format(time.format("YYYY-MM-DD_HH:mm:ss")) for time in bkg_times
    ]
    run(f"rm -f GRIBFILE.* {config.UNGRIB_PATH}/FILE:* {config.UNGRIB_PATH}/PFILE:*")
    if data_source == "fnl":
        link_files = get_rda_data.get_expected_files()
        run(f'./link_grib.csh {" ".join([str(i.absolute()) for i in link_files])}')
    else:
        link_files = get_gfs_data.get_expected_files()
        run(f'./link_grib.csh {" ".join([str(i.absolute()) for i in link_files])}')
    if not os.path.isfile("Vtable"):
        run("ln -sf ungrib/Variable_Tables/Vtable.GFS Vtable")

    run("./ungrib.exe")
    if check_files(ungrib_expected_files, path=config.UNGRIB_PATH):
        logger.success("-----run ungrib success-----")
        run(f"rm -f {config.METGRID_PATH}/met_em.*")
        run("./metgrid.exe")
        if check_files(metgrid_expected_files, path=config.METGRID_PATH):
            logger.success("-----run metgrid success-----")
        else:
            raise Exception("metgrid.exe failed!")
    else:
        raise Exception("ungrib.exe failed!")
