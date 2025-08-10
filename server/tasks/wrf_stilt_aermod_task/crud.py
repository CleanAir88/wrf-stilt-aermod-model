import os
import sys
from pathlib import Path

import pendulum
import requests
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from tasks.common_utils.coordTransform_utils import wgs84toUTMZone50


def clean_old_wrf_files(directory_path: Path, days_threshold: int = 3):
    """
    删除指定目录下超过指定天数的文件

    Args:
        directory_path: 要清理的目录路径
        days_threshold: 文件保留天数阈值，默认3天
    """
    if not directory_path.exists() or not directory_path.is_dir():
        logger.warning(f"目录不存在或不是有效目录: {directory_path}")
        return

    now = pendulum.now()
    deleted_count = 0
    skipped_count = 0

    logger.info(f"开始清理 {directory_path} 中超过 {days_threshold} 天的文件")

    for item in directory_path.glob("**/*"):  # 递归搜索所有文件和目录
        if item.is_file():
            # 获取文件的最后修改时间
            mtime = pendulum.from_timestamp(item.stat().st_mtime)
            days_old = (now - mtime).days

            if days_old > days_threshold:
                try:
                    item.unlink()  # 删除文件
                    deleted_count += 1
                    logger.debug(
                        f"已删除: {item} (最后修改: {mtime.to_date_string()}, {days_old}天前)"
                    )
                except Exception as e:
                    logger.error(f"删除文件 {item} 时出错: {e}")
            else:
                skipped_count += 1
    logger.info(f"清理完成: 已删除 {deleted_count} 个文件, 保留 {skipped_count} 个文件")


def get_model_config():
    """获取STILT模型列表"""
    url = "http://127.0.0.1:8000/api/model_wrf_stilt/model_wrf_stilt/"
    response = requests.get(url).json()
    if len(response) > 0:
        return response[0]
    return None


def get_receptors():
    url = "http://127.0.0.1:8000/api/model_wrf_stilt/receptor/"
    receptors = requests.get(url).json()
    res_data = []
    for i in receptors:
        i["id_s"] = f"R{i['id']}"
        if i["longitude"] and i["latitude"]:
            i["utm_zoom50_x"], i["utm_zoom50_y"] = wgs84toUTMZone50(i["longitude"], i["latitude"])
            i["coord_id"] = f"{int(float(i['utm_zoom50_x']))}_{int(float(i['utm_zoom50_y']))}"
            res_data.append(i)
    return res_data


def get_pollution_source():
    url = "http://127.0.0.1:8000/api/model_wrf_stilt/pollutant_source/"
    pollution_sources = requests.get(url).json()
    res_data = []
    for i in pollution_sources:
        i["id_s"] = f"P{i['id']}"
        if i["longitude"] and i["latitude"]:
            i["utm_zoom50_x"], i["utm_zoom50_y"] = wgs84toUTMZone50(i["longitude"], i["latitude"])
            res_data.append(i)
    return res_data
