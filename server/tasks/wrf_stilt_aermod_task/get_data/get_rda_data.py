import os
import sys
from pathlib import Path

from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tasks.common_utils.common import check_files, download_file


def get_expected_files() -> list[Path]:
    """
    Generate a list of expected file paths based on the configured start and end dates.
    """
    expected_files = []
    st = config.START_DATE
    et = config.END_DATE
    ct = st
    while ct <= et:
        expected_files.append(Path(config.DS083_2_PATH, f"fnl_{ct.format('YYYYMMDD_HH_mm')}.grib2"))
        ct = ct.add(hours=6)
    return expected_files


def run_download_ds083_2_data(fnl_url):
    logger.info("Start downloading ds083.2 files")
    st = config.START_DATE
    et = config.END_DATE
    run_dir = Path(config.DS083_2_PATH)
    run_dir.mkdir(parents=True, exist_ok=True)
    filelist = []
    ct = st
    while ct <= et:
        # Example: https://data.rda.ucar.edu/d083002/grib2/
        filename = (
            f"{fnl_url}{ct.year}/{ct.format('YYYY.MM')}/fnl_{ct.format('YYYYMMDD_HH_mm')}.grib2"
        )
        filelist.append(filename)
        ct = ct.add(hours=6)

    for file_url in filelist:
        fname = os.path.basename(file_url)
        download_file(file_url, run_dir / fname)
    if check_files(get_expected_files()):
        logger.success("-----Download ds083.2 success-----")
    else:
        raise Exception("Download ds083.2 failed!")


def run_download_ds351_data(data_url):
    logger.info("Start downloading ds351 files")
    st = config.START_DATE
    et = config.END_DATE
    run_dir = Path(config.OBS_UPPER_DATA_PATH)
    run_dir.mkdir(parents=True, exist_ok=True)
    filelist = []
    ct = st
    while ct <= et:
        # Example: https://daejeon-kreonet-net.nationalresearchplatform.org:8443/ncar/rda/d351000/little_r/2025/OBS:2025012006
        filename = f"{data_url}/{ct.format('YYYY')}/OBS:{ct.format('YYYYMMDDHH')}"
        filelist.append(filename)
        ct = ct.add(hours=6)

    for file_url in filelist:
        fname = os.path.basename(file_url)
        download_file(file_url, run_dir / fname)
    if check_files(get_expected_files()):
        logger.success("-----Download ds351 success-----")
    else:
        raise Exception("Download ds351 failed!")
