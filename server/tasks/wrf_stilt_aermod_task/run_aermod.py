import os
from pathlib import Path

import config
from apps.model_wrf_stilt.models import EmissionContributionData
from loguru import logger
from netCDF4 import Dataset
from tasks.common_utils.coordTransform_utils import calc_point_distance
from tasks.common_utils.shell import create_link_and_backup, run
from tasks.wrf_stilt_aermod_task.crud import get_pollution_source, get_receptors
from tasks.wrf_stilt_aermod_task.model_template.aermod_conf import (
    aermap_inp,
    aermod_inp,
    mmif_inp,
)
from tqdm import tqdm
from wrf import ll_to_xy


def extract_receptor_data(file_path, nums):
    """从AERMOD输出文件中提取受体点数据"""
    data = []
    reading_data = False
    with open(file_path, "r") as f:
        for line in f:
            # 查找数据部分的开始标志
            if "*** DISCRETE CARTESIAN RECEPTOR POINTS ***" in line:
                reading_data = True
                # 跳过标题行
                next(f)  # 跳过标题行
                next(f)  # 跳过分隔符行
                continue

            # 当找到这些行时，表示数据部分结束
            if reading_data and ("*** AERMOD" in line or "***Message Summary" in line):
                reading_data = False
                continue

            # 提取数据
            if reading_data:
                # 忽略空行或只包含横线的行
                if not line.strip() or "-" in line or "X-COORD" in line:
                    continue
                row = line.strip().split()
                if len(row) > 6:
                    continue
                data1 = row[:3]
                data2 = row[3:]
                data.append(data1)
                data.append(data2)
                # 收集的数据量等于受体数
                if len(data) >= nums:
                    break
    return data


def gene_emis(p):
    emission_allocation_coefficient_hour = config.emission_allocation_coefficient_hour
    emi_file = open("aermod.emi", "w")
    # pm25_day_g = float(p["pm25"]) / 365 * 1e6
    pm10_day_g = float(p["emis_value"]) / 365 * 1e6
    emission_type = p["emission_type"]
    coefficient = emission_allocation_coefficient_hour.get(
        emission_type, emission_allocation_coefficient_hour["其他"]
    )
    st, et = get_wrf_date_range(tm=config.START_DATE)
    while st <= et:
        hour = st.hour
        emis_value = pm10_day_g * coefficient[hour - 1]
        emi_file.write(
            "SO HOUREMIS"
            f" {st.year} {st.month} {st.day} {hour} {p['id_s']} {emis_value:8.2f} {emis_value:8.2f} {emis_value:8.2f}\n"
        )
        st = st.add(hours=1)
    emi_file.close()


def run_aermap(model_config, receptors, pollution_sources):
    logger.info("run aermap.")
    # LOCATION   STACK1  POINT  410000 4010000
    # DISCCART  506728 4058713
    # 409870 3984410 50 587798 4206286 50
    aermod_domainxy, aermod_anchorxy = (
        model_config["aermod_domainxy"],
        model_config["aermod_anchorxy"],
    )
    aermod_domainxy_list = aermod_domainxy.split(" ")
    x_range = [int(aermod_domainxy_list[0]), int(aermod_domainxy_list[3])]
    y_range = [int(aermod_domainxy_list[1]), int(aermod_domainxy_list[4])]
    os.chdir(config.AERMOD_WD + "/aermap")
    so_points = ""

    def is_in_zoom50_range(x, y):
        return x_range[0] <= x <= x_range[1] and y_range[0] <= y <= y_range[1]

    for i in pollution_sources:
        if not is_in_zoom50_range(i["utm_zoom50_x"], i["utm_zoom50_y"]):
            continue
        so_points += f"LOCATION   {i['id_s']}  POINT  {i['utm_zoom50_x']} {i['utm_zoom50_y']}\n   "
    re_points = ""
    for i in receptors:
        if not is_in_zoom50_range(i["utm_zoom50_x"], i["utm_zoom50_y"]):
            continue
        re_points += f"DISCCART  {i['utm_zoom50_x']} {i['utm_zoom50_y']}\n   "
    aermap_datafile = model_config["aermap_datafile"].split("aermap_data/")[1]
    aermap_inp_content = aermap_inp.format(
        datafile=config.BASE_PATH + "/server/uploads/aermap_data/" + aermap_datafile,
        aermod_domainxy=aermod_domainxy,
        aermod_anchorxy=aermod_anchorxy,
        so_points=so_points,
        re_points=re_points,
    )
    config_f = Path("aermap.inp")
    fw = open(config_f, "w", encoding="utf-8")
    fw.write(aermap_inp_content)
    fw.close()
    run("./aermap aermap.inp")


def calc_grid_ij(points, wrf_file_path):
    wrf_file = Dataset(wrf_file_path)

    ij_list = [ll_to_xy(wrf_file, p["latitude"], p["longitude"]) for p in points]
    i_vals = [int(ij[0].values) if hasattr(ij[0], "values") else int(ij[0]) for ij in ij_list]
    j_vals = [int(ij[1].values) if hasattr(ij[1], "values") else int(ij[1]) for ij in ij_list]

    buffer = 10
    i_min = max(0, min(i_vals) - buffer)
    i_max = max(i_vals) + buffer
    j_min = max(0, min(j_vals) - buffer)
    j_max = max(j_vals) + buffer

    NX = wrf_file.dimensions["west_east"].size
    NY = wrf_file.dimensions["south_north"].size
    i_max = min(i_max, NX - 1)
    j_max = min(j_max, NY - 1)
    return f"{i_min},{j_min} {i_max},{j_max}"


def get_wrf_date_range(tm):
    # tm_hour = tm.hour
    # if tm_hour == 0:
    #     tm_hour = 24
    wrf_hour = (tm.hour) // 6 * 6
    wrf_st = tm.replace(hour=wrf_hour)
    wrf_et = wrf_st.add(hours=6)
    return wrf_st, wrf_et


def run_mmif(model_config, receptors):
    logger.info("-----run mmif start-----")
    os.chdir(config.MMIF_PATH)
    wrf_st, wrf_et = get_wrf_date_range(tm=config.START_DATE)
    # wrf_file = "wrfout_d03_2024-01-01_00:00:00" 0 - 6点
    wrf_tm = wrf_st.format("YYYY-MM-DD_HH:mm:ss")
    wrf_file = config.WRFOUT_DATA_PATH + f"/wrfout_d0{model_config['stilt_wrf_dom']}_{wrf_tm}"
    point_list = []
    for receptor in receptors:
        point_list.append(
            f"POINT   LL         {receptor['latitude']}  {receptor['longitude']} 0     !"
            f" {receptor['name']}"
        )
    points = "\n".join(point_list)
    grid_ij = calc_grid_ij(receptors, wrf_file)
    conf_content = mmif_inp.format(
        wrf_file=wrf_file,
        start=wrf_st.format("YYYYMMDDHH"),
        end=wrf_et.format("YYYYMMDDHH"),
        points=points,
        grid_ij=grid_ij,
    )
    output_file_sfc = Path("aermod.sfc")
    output_file_pfl = Path("aermod.pfl")
    if output_file_sfc.exists():
        os.remove(output_file_sfc)
    if output_file_pfl.exists():
        os.remove(output_file_pfl)

    config_f = Path("mmif1.inp")
    fw = open(config_f, "w", encoding="utf-8")
    fw.write(conf_content)
    fw.close()
    run("./mmif mmif1.inp")

    if output_file_sfc.exists() and output_file_pfl.exists():
        logger.success("-----run mmif success-----")
        create_link_and_backup(
            source_file=output_file_sfc,
            target_file=Path(config.AERMOD_WD + "/aermod", "aermod.sfc"),
        )
        create_link_and_backup(
            source_file=output_file_pfl,
            target_file=Path(config.AERMOD_WD + "/aermod", "aermod.pfl"),
        )
    else:
        logger.error("-----run mmif failed-----")
        raise Exception("mmif failed！")


def get_aermod_result(pollution_sources, receptors):
    res_data = {}
    for p in tqdm(pollution_sources):
        logger.info(f'-----run pollution sources {p["name"]}-----')
        pid = p["id_s"]
        if p["time_type"] == "yearly":
            gene_emis(p)
            emis_rate = p["emis_value"] / 365 / 24 / 3600 * 1e6
            houremis = f"HOUREMIS  aermod.emi {pid}"
        else:
            emis_rate = p["emis_value"] / 3600 * 1e6  # 单位：g/s
            houremis = ""
        aermod_conf_content = aermod_inp.format(
            location=(
                f"LOCATION  {pid}   point  {int(p['utm_zoom50_x'])}   {int(p['utm_zoom50_y'])}  "
                f" {p['height']}"
            ),
            srcparam=(
                f"SRCPARAM  {pid}     {emis_rate}    {p['height']}   {p['stack_temp']}"
                f" {p['exit_velocity']}  {p['diameter']} "
            ),
            houremis=houremis,
        )
        config_f = Path("aermod.inp")
        fw = open(config_f, "w", encoding="utf-8")
        fw.write(aermod_conf_content)
        fw.close()
        run("./aermod aermod.inp aermod.out")

        aermod_sum = Path("aermod.out")
        if not aermod_sum.exists():
            logger.error(f"-----aermod run error-----")
            raise Exception("aermod运行失败，请检查！")

        aermod_sum_data = extract_receptor_data(aermod_sum, nums=len(receptors))
        for d in aermod_sum_data:
            if len(d) < 3:
                continue
            x, y, conc = d
            receptor_id = f"{int(float(x))}_{int(float(y))}"
            if receptor_id not in res_data:
                res_data[receptor_id] = []
            res_data[receptor_id].append([conc, pid])
    return res_data


def run_aermod(model_config, receptors, pollution_sources):
    logger.info("-----run aermod start-----")
    os.chdir(config.AERMOD_WD + "/aermod")

    receptors_dict = {i["coord_id"]: i for i in receptors}

    dist_dict = {}
    for r in receptors:
        point1 = [r["longitude"], r["latitude"]]
        for p in pollution_sources:
            point2 = [p["longitude"], p["latitude"]]
            dist = calc_point_distance(point1, point2)
            dist_dict["{}_{}".format(p["id"], r["id"])] = dist

    res_data = get_aermod_result(pollution_sources, receptors)
    # 对受体的污染源贡献排名，取前10
    save_data_list = []
    for receptor_coord_id, conc_list in res_data.items():
        conc_rank_list = sorted(conc_list, reverse=True)[:10]
        emis_value_sum = sum([float(i[0]) for i in conc_rank_list])
        for rank in conc_rank_list:
            receptor = receptors_dict.get(receptor_coord_id)
            if not receptor:
                continue
            pollutant_source_id = int(rank[1].replace("P", ""))
            dist = round(dist_dict.get(f"{pollutant_source_id}_{receptor['id']}"), 1)
            save_data = {
                "pollutant_source_id": pollutant_source_id,
                "receptor_id": receptor["id"],
                "time": config.START_DATE.to_datetime_string(),
                "emis_value": float(rank[0]),
                "emis_value_sum": emis_value_sum,
                "emis_rate": round(float(rank[0]) / emis_value_sum * 100, 2),  # 占比%
                "dist": dist,
            }
            logger.info(save_data)
            save_data_list.append(save_data)
    run_sensitivity_aermod(save_data_list, pollution_sources, receptors_dict)
    EmissionContributionData.objects.filter(time=config.START_DATE.to_datetime_string()).delete()
    EmissionContributionData.objects.bulk_create(
        [EmissionContributionData(**i) for i in save_data_list],
        batch_size=1000,
        ignore_conflicts=True,
    )
    logger.info("-----run aermod end-----")


# aermod 敏感性分析
# 对污染源排放*2后重新计算排放量和排放占比
def run_sensitivity_aermod(emis_data_list, pollution_sources, receptors_dict):
    logger.info("-----run aermod sensitivity analysis start-----")
    pollution_source_id_list = [emis_data["pollutant_source_id"] for emis_data in emis_data_list]
    logger.info(pollution_source_id_list)
    sensitivity_pollution_source_list = []
    for p in pollution_sources:
        if p["id"] not in pollution_source_id_list:
            continue
        sensitivity_pollution_source = p.copy()
        sensitivity_pollution_source["emis_value"] = p["emis_value"] * 2
        sensitivity_pollution_source["id"] = f"P{sensitivity_pollution_source['id']}"
        sensitivity_pollution_source_list.append(sensitivity_pollution_source)
    sensitivity_res_data = get_aermod_result(
        sensitivity_pollution_source_list, receptors_dict.values()
    )
    sensitivity_data_dict = {}
    for receptor_coord_id, conc_list in sensitivity_res_data.items():
        conc_rank_list = sorted(conc_list, reverse=True)
        for rank in conc_rank_list:
            receptor = receptors_dict.get(receptor_coord_id)
            if not receptor:
                continue
            receptor_id = receptor["id"]
            pollutant_source_id = int(rank[1].replace("P", ""))
            sensitivity_data = {
                "pollutant_source_id": pollutant_source_id,
                "receptor_id": receptor_id,
                "time": config.START_DATE.to_datetime_string(),
                "emis_value_s": float(rank[0]),
            }
            sensitivity_data_dict[f"{pollutant_source_id}_{receptor_id}"] = sensitivity_data

    for emis_data in emis_data_list:
        receptor_id = emis_data["receptor_id"]
        pollutant_source_id = emis_data["pollutant_source_id"]
        sensitivity_key = f"{pollutant_source_id}_{receptor_id}"
        if sensitivity_key in sensitivity_data_dict:
            sensitivity_data = sensitivity_data_dict[sensitivity_key]
            emis_data["emis_value_s"] = sensitivity_data["emis_value_s"]
            emis_data["emis_rate_s"] = round(
                float(emis_data["emis_value_s"])
                / (
                    emis_data["emis_value_sum"]
                    - emis_data["emis_value"]
                    + emis_data["emis_value_s"]
                )
                * 100,
                2,
            )
        del emis_data["emis_value_sum"]


def run_aermod_all(model_config):
    receptors = get_receptors()
    pollution_sources = get_pollution_source()
    run_aermap(model_config, receptors, pollution_sources)
    run_mmif(model_config, receptors)
    run_aermod(model_config, receptors, pollution_sources)
