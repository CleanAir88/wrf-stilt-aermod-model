import json
from pathlib import Path

import numpy as np
from netCDF4 import Dataset


def nc_data_to_json(filename: Path, target_path: Path) -> Path:
    """获取NetCDF(Network Common Data Form) 文件的数据"""
    fh = Dataset(filename, mode="r")
    # 获取每个变量的值
    lons = fh.variables["lon"][:]
    lats = fh.variables["lat"][:]
    foot = fh.variables["foot"][:]

    # lons 保留6位小数
    lons = np.round(lons, 6)
    lats = np.round(lats, 6)

    # 有效值过滤
    foot_masked = foot > 0
    time_indices, lat_indices, lng_indices = np.where(foot_masked)

    # 获取有效值
    data = [
        (lons[j], lats[i], float(foot[t, i, j]))  # 将numpy类型转换为Python原生类型
        for t, i, j in zip(time_indices, lat_indices, lng_indices)
    ]

    fh.close()
    res = {"columns": ["lng", "lat", "val"], "data": data}
    json_name = Path(target_path, filename.stem + ".json")
    with open(json_name, "w") as f:
        json.dump(res, f)
    return json_name
