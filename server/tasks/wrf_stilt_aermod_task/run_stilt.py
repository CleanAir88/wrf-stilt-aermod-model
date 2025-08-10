import os
import sys
from pathlib import Path
from typing import Optional

from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tasks.common_utils.common import (
    check_files_exist_one,
    get_stilt_out_filename,
    render_template,
)
from tasks.common_utils.decorator import timer
from tasks.common_utils.exceptions import JobException
from tasks.common_utils.model_types import Namelist
from tasks.common_utils.process_stilt_data import nc_data_to_json
from tasks.common_utils.shell import create_link_and_backup, run
from tasks.wrf_stilt_aermod_task.crud import get_receptors


@timer()
def run_instance(namelist: Namelist):
    logger.info(f"namelist: {namelist.model_dump()}")
    os.makedirs(config.STILT_DATA_PATH, exist_ok=True)
    # 1 生成 r 执行文件
    file_content = render_template(
        Path(Path(__file__).parent, "model_template/run_stilt.r.T"), namelist.model_dump()
    )
    r_config_file = Path(config.STILT_WD, "r", "run_stilt.r")
    with open(r_config_file, "w") as f:
        f.write(file_content)

    # 2 执行 r 文件
    run(cmd=r_config_file)

    # 3 检查输出结果 由于gfs文件可能有缺失 仅验证是否有文件生成 不验证数量
    output_files = get_stilt_out_filename(namelist, stilt_wd=config.STILT_WD)
    flag, error_files = check_files_exist_one(output_files, all_exist=False)
    if not flag:
        logger.error(f"Files not generate: {error_files}")
        raise JobException("Files not generate.")

    # 4 将结果转为json格式 保存到指定目录
    stilt_out_path = Path(config.STILT_WD, "out/by-id")
    dirs = list(stilt_out_path.iterdir())
    for file_dir in dirs:
        date_path = file_dir.name[:8]
        target_path = Path(config.STILT_DATA_PATH, date_path)
        if not target_path.is_dir():
            target_path.mkdir(parents=True)
        for f in Path(stilt_out_path, file_dir).iterdir():
            if f.suffix == ".nc":
                nc_file = Path(stilt_out_path, file_dir, f)
                nc_data_to_json(filename=nc_file, target_path=target_path)


def run_stilt(model_config, receptor_ids: Optional[str] = None):
    """
    运行 STILT 模型
    run_date: 运行日期 使用UTC时区， 计算时段为 (run_date - 6h) ~ run_date
    """
    os.chdir(Path(config.STILT_WD))
    if not Path("arlout").is_dir():
        Path("arlout").mkdir()

    run_date = config.END_DATE

    # wrf to arl
    config_f2 = Path(Path(__file__).parent, "model_template/WRFDATA.CFG")
    target_f2 = Path(config.STILT_WD, "exe/WRFDATA.CFG")
    if not target_f2.is_file():
        create_link_and_backup(source_file=config_f2, target_file=target_f2)
    date_str = run_date.subtract(hours=6).format("YYYY-MM-DD_HH:mm:ss")
    wrfout_file = f"wrfout_d0{model_config['stilt_wrf_dom']}_{date_str}"
    wrfout_file_arl = f"{wrfout_file}.ARL"
    if not Path(config.WRFOUT_DATA_PATH, wrfout_file).is_file():
        logger.error(f"wrfout file :{wrfout_file} not exist.")
        raise JobException("wrfout file not exist.")
    run(f"exe/arw2arl -i{config.WRFOUT_DATA_PATH}/{wrfout_file} -oarlout/{wrfout_file_arl}")

    t_start = run_date.subtract(hours=6)
    t_end = run_date
    receptor_list = get_receptors()
    if receptor_ids:
        receptor_ids = receptor_ids.split(",")
        receptor_list = [r for r in receptor_list if str(r["id"]) in receptor_ids]
    for receptor in receptor_list:
        namelist = Namelist(
            stilt_wd=config.STILT_WD,
            n_cores=model_config["n_cores"],
            t_start=t_start,
            t_end=t_end,
            lati=receptor["latitude"],
            long=receptor["longitude"],
            zagl=receptor["height"],
            xmn=receptor["region"]["xmn"],
            xmx=receptor["region"]["xmx"],
            ymn=receptor["region"]["ymn"],
            ymx=receptor["region"]["ymx"],
            xres=model_config["xres"],
            yres=model_config["yres"],
        )
        try:
            print(f"namelist: {namelist.model_dump()}")
            run_instance(namelist)
        except Exception as e:
            logger.error(f"Job failed: {e}")
            # raise JobException(e)
            continue


if __name__ == "__main__":
    run_stilt(run_date="2025-01-03")
