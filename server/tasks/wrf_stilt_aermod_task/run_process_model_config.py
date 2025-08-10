import os
import sys
from pathlib import Path

from jinja2 import Template
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from tasks.common_utils.shell import create_link_and_backup

curr_path = Path(__file__).parent


def render_template(template_file: str, data: dict) -> str:
    print("rendering template ", template_file)

    with open(template_file, "r") as tf:
        template = Template(tf.read())
        return template.render(data)


def process_conf_list_to_str(item_list: list) -> str:
    conf_str = "".join([f"{str(i) + ', ':<5}" for i in item_list[:-1]]) + f"{item_list[-1]}"
    return conf_str


def process_wps_namelist(config_data):
    logger.info("update wps namelist.")
    config_f = Path(curr_path, "model_template/namelist.wps")
    config_t_file = Path(curr_path, "model_template/namelist.wps.T")
    MAX_DOM = config_data["max_dom"]
    start_date_str = config.START_DATE.format("YYYY-MM-DD_HH:mm:ss")
    end_date_str = config.END_DATE.format("YYYY-MM-DD_HH:mm:ss")

    parent_id = "1,   " + process_conf_list_to_str([str(i + 1) for i in range(MAX_DOM - 1)])
    parent_grid_ratio = "1,   " + process_conf_list_to_str(["3"] * (MAX_DOM - 1))

    config_data.update({
        "start_date": process_conf_list_to_str([f"'{start_date_str}'"] * MAX_DOM),
        "end_date": process_conf_list_to_str([f"'{end_date_str}'"] * MAX_DOM),
        "active_grid": process_conf_list_to_str([".true."] * MAX_DOM),
        "parent_id": parent_id,
        "parent_grid_ratio": parent_grid_ratio,
        "s_we": process_conf_list_to_str(["1"] * MAX_DOM),
        "s_sn": process_conf_list_to_str(["1"] * MAX_DOM),
        "geog_data_res": process_conf_list_to_str(["'default'"] * MAX_DOM),
        "prefix": f"{config.DATA_PATH}/ungrib_file/FILE",
        "fg_name": f"{config.DATA_PATH}/ungrib_file/FILE",
        "opt_output_from_metgrid_path": f"{config.DATA_PATH}/metgrid_file",
        "ref_lat": 34.00,
        "ref_lon": 110.00,
    })

    file_content = render_template(config_t_file, config_data)
    with open(config_f, "w") as fw:
        fw.write(file_content)
    old_f = Path(config.WPS_PATH, "namelist.wps")
    create_link_and_backup(source_file=config_f, target_file=old_f)


def process_obsgrid_namelist(config_data):
    logger.info("update obsgrid namelist.")
    config_f = Path(curr_path, "model_template/namelist.oa")
    config_t_file = Path(curr_path, "model_template/namelist.oa.T")

    config_data["start_year"] = config.START_DATE.year
    config_data["start_month"] = config.START_DATE.format("MM")
    config_data["start_day"] = config.START_DATE.format("DD")
    config_data["start_hour"] = config.START_DATE.format("HH")
    config_data["end_year"] = config.END_DATE.year
    config_data["end_month"] = config.END_DATE.format("MM")
    config_data["end_day"] = config.END_DATE.format("DD")
    config_data["end_hour"] = config.END_DATE.format("HH")
    config_data["obs_filename"] = f"{config.OBS_DATA_PATH}/OBS"

    file_content = render_template(config_t_file, config_data)
    with open(config_f, "w") as fw:
        fw.write(file_content)
    old_f = Path(config.OBSGRID_PATH, "namelist.oa")
    create_link_and_backup(source_file=config_f, target_file=old_f)


def process_wrf_namelist(obsgrid, config_data):
    logger.info("update wrf namelist.")
    config_f = Path(curr_path, "model_template/namelist.input")
    if obsgrid:
        config_t_file = Path(curr_path, "model_template/namelist_obs.input.T")
    else:
        config_t_file = Path(curr_path, "model_template/namelist.input.T")
    if obsgrid:
        sf_surface_physics = "7"
        sf_sfclay_physics = "7"
        bl_pbl_physics = "7"
    else:
        sf_surface_physics = "2"  # Noah Land Surface Model（LSM）
        sf_sfclay_physics = "91"  # MYNN Surface Layer
        bl_pbl_physics = "5"  # MYNN PBL
    MAX_DOM = config_data["max_dom"]
    dx = config_data["dx"]
    dy = config_data["dy"]
    START_DATE = config.START_DATE
    END_DATE = config.END_DATE
    config_data["run_days"] = (END_DATE - START_DATE).days
    config_data["run_hours"] = (END_DATE - START_DATE).seconds // 3600
    config_data["run_minutes"] = ((END_DATE - START_DATE).seconds // 60) % 60
    config_data["run_seconds"] = (END_DATE - START_DATE).seconds % 60

    config_data["start_year"] = ", ".join([f"{START_DATE.year}" for i in range(MAX_DOM)])
    config_data["start_month"] = ",   ".join([f"{START_DATE.format('MM')}" for i in range(MAX_DOM)])
    config_data["start_day"] = ",   ".join([f"{START_DATE.format('DD')}" for i in range(MAX_DOM)])
    config_data["start_hour"] = ",   ".join([f"{START_DATE.format('HH')}" for i in range(MAX_DOM)])
    config_data["start_minute"] = ",   ".join(
        [f"{START_DATE.format('mm')}" for i in range(MAX_DOM)]
    )
    config_data["start_second"] = ",   ".join(
        [f"{START_DATE.format('ss')}" for i in range(MAX_DOM)]
    )

    config_data["end_year"] = ", ".join([f"{END_DATE.year}" for i in range(MAX_DOM)])
    config_data["end_month"] = ",   ".join([f"{END_DATE.format('MM')}" for i in range(MAX_DOM)])
    config_data["end_day"] = ",   ".join([f"{END_DATE.format('DD')}" for i in range(MAX_DOM)])
    config_data["end_hour"] = ",   ".join([f"{END_DATE.format('HH')}" for i in range(MAX_DOM)])
    config_data["end_minute"] = ",   ".join([f"{END_DATE.format('mm')}" for i in range(MAX_DOM)])
    config_data["end_second"] = ",   ".join([f"{END_DATE.format('ss')}" for i in range(MAX_DOM)])

    config_data["input_from_file"] = process_conf_list_to_str([".true."] * MAX_DOM)
    config_data["history_interval"] = process_conf_list_to_str(["60"] * MAX_DOM)
    config_data["frames_per_outfile"] = process_conf_list_to_str(["24"] * MAX_DOM)
    config_data["e_vert"] = process_conf_list_to_str(["30"] * MAX_DOM)

    config_data["dx"] = process_conf_list_to_str([int(dx / 3**i) for i in range(MAX_DOM)])
    config_data["dy"] = process_conf_list_to_str([int(dy / 3**i) for i in range(MAX_DOM)])
    config_data["grid_id"] = process_conf_list_to_str([str(i + 1) for i in range(MAX_DOM)])
    config_data["parent_id"] = "1,   " + process_conf_list_to_str(
        [str(i + 1) for i in range(MAX_DOM - 1)]
    )
    config_data["parent_grid_ratio"] = "1,   " + process_conf_list_to_str(["3"] * (MAX_DOM - 1))
    config_data["parent_time_step_ratio"] = "1,   " + process_conf_list_to_str(
        ["3"] * (MAX_DOM - 1)
    )

    config_data["mp_physics"] = process_conf_list_to_str(["10"] * MAX_DOM)
    config_data["ra_lw_physics"] = process_conf_list_to_str(["4"] * MAX_DOM)
    config_data["ra_sw_physics"] = process_conf_list_to_str(["4"] * MAX_DOM)
    config_data["radt"] = process_conf_list_to_str(["10"] * MAX_DOM)
    config_data["sf_sfclay_physics"] = process_conf_list_to_str([sf_sfclay_physics] * MAX_DOM)
    config_data["sf_surface_physics"] = process_conf_list_to_str([sf_surface_physics] * MAX_DOM)
    config_data["bl_pbl_physics"] = process_conf_list_to_str([bl_pbl_physics] * MAX_DOM)
    config_data["bldt"] = process_conf_list_to_str(["0"] * MAX_DOM)
    config_data["cu_physics"] = process_conf_list_to_str(["1"] * MAX_DOM)
    config_data["specified"] = process_conf_list_to_str([".true."] + [".false."] * (MAX_DOM - 1))
    config_data["nested"] = process_conf_list_to_str([".false."] + [".true."] * (MAX_DOM - 1))

    file_content = render_template(config_t_file, config_data)
    with open(config_f, "w") as fw:
        fw.write(file_content)
    old_f = Path(config.WRF_PATH, "run/namelist.input")
    create_link_and_backup(source_file=config_f, target_file=old_f)


def process_all_config(model_config, obsgrid):
    process_wps_namelist(model_config)
    process_obsgrid_namelist(model_config)
    process_wrf_namelist(config_data=model_config, obsgrid=obsgrid)
