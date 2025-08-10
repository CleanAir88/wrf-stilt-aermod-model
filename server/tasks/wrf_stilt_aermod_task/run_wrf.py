import os
import sys
from pathlib import Path

from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tasks.common_utils.common import check_files
from tasks.common_utils.shell import run


def run_wrf(obsgrid: bool, core_nums: int, max_dom: int):
    wrf_run_path = Path(config.WRF_PATH, "run")
    os.chdir(wrf_run_path)
    os.makedirs(config.WRFOUT_DATA_PATH, exist_ok=True)
    run("rm -f met_em.* metoa_em.* wrfsfdda_d* rsl.error.* rsl.out.* wrfbdy_d* wrffdda_d*")
    if obsgrid:
        run(f"ln -s {config.OBSGRID_PATH}/metoa_em.* ./")
        run(f"ln -s {config.OBSGRID_PATH}/wrfsfdda_d0* ./")
    else:
        run(f"ln -s {config.METGRID_PATH}/met_em.* ./")
    run("./real.exe")

    start_time_str = config.START_DATE.format("YYYY-MM-DD_HH:mm:ss")
    wrf_real_expected_files = ["wrfinput_d{:02d}".format(i + 1) for i in range(max_dom)]
    if check_files(wrf_real_expected_files):
        logger.success("-----run wrf_real success-----")
        # export OMPI_ALLOW_RUN_AS_ROOT=1
        # export OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1
        os.environ["OMPI_ALLOW_RUN_AS_ROOT"] = "1"
        os.environ["OMPI_ALLOW_RUN_AS_ROOT_CONFIRM"] = "1"
        run(f"mpirun -n {core_nums} ./wrf.exe")
        wrf_expected_files = [
            "wrfout_d{:02d}_{}".format(i + 1, start_time_str) for i in range(max_dom)
        ]
        if check_files(wrf_expected_files):
            run(f"mv wrfout_d0* {config.WRFOUT_DATA_PATH}")
            logger.success("-----run wrf success-----")
        else:
            raise Exception("WRF failed, please check the log files.")
    else:
        raise Exception("WRF real failed, please check the log files.")
