import json
import math
import os
import sys
from pathlib import Path

import requests
from loguru import logger

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config


def calcpws(tem):
    if tem < -3:
        lpws = (
            0.000000000014342 * (tem**6)
            + 0.0000000021948 * (tem**5)
            + 0.00000012847 * (tem**4)
            + 0.0000042761 * (tem**3)
            - 0.000076135 * (tem**2)
            + 0.036138 * tem
            + 2.787
        )
    else:
        lpws = (
            -0.0000000012587 * (tem**6)
            + 0.00000011796 * (tem**5)
            - 0.000004208 * (tem**4)
            + 0.000071216 * (tem**3)
            - 0.00068811 * (tem**2)
            + 0.03328 * tem
            + 2.7852
        )
    return 10**lpws


def pws2dp(pws):
    lpws = math.log10(pws)
    if pws < 565:
        return 2.1349 * (lpws**2) + 15.463 * lpws - 59.781
    else:
        return 5.492 * (lpws**2) + 0.302 * lpws - 43.362


def fetch_std_data(tm, obsdata_url_config):
    url = (
        obsdata_url_config["base_url"]
        + f"&{obsdata_url_config['param_time']}={tm.to_datetime_string()}"
    )
    logger.info(f"Fetching data from {url}")
    r = requests.get(url).json()
    return r["data"]


def process_std_data(res_list, outfile, tm, obsdata_url_config):
    nv = -888888.0
    nvi = -888888
    eof = -777777.0
    stnum = 2170
    field_humidity = obsdata_url_config["field_humidity"]
    field_temperature = obsdata_url_config["field_temperature"]
    field_latitude = obsdata_url_config["field_latitude"]
    field_longitude = obsdata_url_config["field_longitude"]
    field_wind_speed = obsdata_url_config["field_wind_speed"]
    field_wind_direction = obsdata_url_config["field_wind_direction"]
    for entry in res_list:
        wind_speed = entry[field_wind_speed]
        wind_dir = entry[field_wind_direction]
        temp = entry[field_temperature]
        hum = entry[field_humidity]
        temp_valid = temp is not None and temp < 50
        if temp_valid and hum is not None:
            pws = calcpws(temp)
            dp = pws2dp(pws * hum / 100) + 273.15
            temp = entry[field_temperature] + 273.15
        else:
            dp = nv
            temp = nv
        if wind_speed is None:
            wind_speed = nv
        if wind_dir is None:
            wind_dir = nv
        lng = entry[field_longitude]
        lat = entry[field_latitude]
        alt = palt = 23
        dir10 = pres = slp = nv
        ymd = tm.format("YYYYMMDDHHmmss")
        # First write statement
        outfile.write(
            f"{lat:20.5f}{lng:20.5f}{'  AIREP     get data information here.  ':<40}{'SOUNDINGS FROM ????????? SOURCE':<40}"
            f"{'FM-96 AIREP':<40}{'':<40}{alt:20.5f}{1:10d}{0:10d}"
            f"{0:10d}{0:10d}{0:10d}{'F':>10}{'F':>10}{'F':>10}{nvi:10d}{nvi:10d}"
            f"{ymd:>20}{slp:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}"
            f"{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}"
            f"{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}\n"
        )
        # Second write statement
        outfile.write(
            f"{pres:13.5f}{0:7d}{alt:13.5f}{0:7d}{temp:13.5f}{0:7d}{dp:13.5f}{0:7d}"
            f"{wind_speed:13.5f}{0:7d}{wind_dir:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}"
            f"{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}\n"
        )
        # Third write statement
        outfile.write(
            f"{eof:13.5f}{0:7d}{eof:13.5f}{0:7d}{1:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}"
            f"{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}{nv:13.5f}{0:7d}\n"
        )
        outfile.write(f"{1:7d}{0:7d}{0:7d}\n")


def create_obs_data(st, et, obsdata_url_config):
    data_path = Path(config.OBS_SURFACE_DATA_PATH)
    filename = Path(data_path, f"OBS:{et.format('YYYY-MM-DD_HH')}")
    if filename.is_file():
        logger.info(f"File exists: {filename.name}")
        return
    logger.info(f"Downloading file: {filename.name}")
    if not data_path.is_dir():
        data_path.mkdir(parents=True)
    outfile = open(filename, "w")
    while st <= et:
        gf_data = fetch_std_data(tm=st.in_tz("PRC"), obsdata_url_config=obsdata_url_config)
        process_std_data(
            res_list=gf_data, outfile=outfile, tm=st, obsdata_url_config=obsdata_url_config
        )
        st = st.add(hours=1)


def run_download_obs_data(model_config):
    st = config.START_DATE
    et = config.END_DATE
    print(st, et)
    obsdata_url_config = model_config["obsdata_url_config"]
    create_obs_data(st=st.subtract(hours=6), et=st, obsdata_url_config=obsdata_url_config)
    create_obs_data(st=st, et=et, obsdata_url_config=obsdata_url_config)
