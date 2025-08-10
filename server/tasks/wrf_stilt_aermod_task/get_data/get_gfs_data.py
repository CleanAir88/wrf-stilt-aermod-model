import os
import sys
from pathlib import Path

from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tasks.common_utils.common import check_files, download_file


def get_expected_files() -> list[Path]:
    expected_files = []
    st = config.START_DATE.subtract(hours=6)
    run_dir = Path(config.GFS_PATH)
    for fhr in range(6, 13):
        fname = f"gfs.t{st.format('HH')}z.pgrb2.0p25.f{fhr:03d}"
        expected_files.append(run_dir / f"{st.format('YYYYMMDDHH')}_{fname}")
    return expected_files


def run_download_gfs_data(gfs_url):
    # 6-12点数据，下载0点的 f006-f012 gfs数据
    logger.info("开始下载gfs文件")
    st = config.START_DATE.subtract(hours=6)
    run_dir = Path(config.GFS_PATH)
    run_dir.mkdir(parents=True, exist_ok=True)
    start_h = st.format("HH")
    for fhr in range(6, 13):
        fname = f"gfs.t{st.format('HH')}z.pgrb2.0p25.f{fhr:03d}"
        # https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/
        url = f"{gfs_url}gfs.{st.format('YYYYMMDD')}/{start_h}/atmos/{fname}"
        logger.info(f"下载文件：{fname}, url: {url}")
        download_file(url, run_dir / f"{st.format('YYYYMMDDHH')}_{fname}")
    if check_files(get_expected_files()):
        logger.success("-----run download gfs success-----")
    else:
        raise Exception("download gfs failed!")
