import os

import geopandas as gpd
import numpy as np
import pyproj

# from tasks.wrf_stilt_aermod_task.utils.wps_projection import WPSDomainLCC


def offset_latlon(lat, lon, dx_km, dy_km):
    """
    从某个经纬度出发，偏移 dx_km（东西向）、dy_km（南北向），返回新的经纬度
    """
    R = 6371.0  # 地球平均半径，单位：km
    deg_per_rad = 180.0 / np.pi

    # 计算纬度偏移（北正南负）
    delta_lat = (dy_km / R) * deg_per_rad

    # 计算经度偏移（东正西负），要考虑纬度的 cos 因素
    delta_lon = (dx_km / (R * np.cos(lat * np.pi / 180))) * deg_per_rad

    new_lat = lat + delta_lat
    new_lon = lon + delta_lon

    return new_lat, new_lon


def calc_grid_offset_from_latlon2(
    dx, dy, outer_latlon=(34, 110), inner_latlon=(36.761754, 117.1006975)
):
    outer_lat, outer_lon = outer_latlon
    inner_lat, inner_lon = inner_latlon
    R = 6371.0

    # 将经纬度转换为弧度
    deg_to_rad = np.pi / 180.0
    outer_lat_rad = outer_lat * deg_to_rad
    outer_lon_rad = outer_lon * deg_to_rad
    inner_lat_rad = inner_lat * deg_to_rad
    inner_lon_rad = inner_lon * deg_to_rad

    # 计算经纬度差
    # 东西
    delta_x_km = R * np.cos((outer_lat_rad + inner_lat_rad) / 2) * (inner_lon_rad - outer_lon_rad)
    # 南北
    delta_y_km = R * (inner_lat_rad - outer_lat_rad)

    # 转换为网格点数偏移
    i_offset = delta_x_km / dx
    j_offset = delta_y_km / dy
    return i_offset, j_offset


def calc_grid_offset_from_latlon(
    dx,
    dy,
    outer_latlon=(34, 110),
    inner_latlon=(36.761754, 117.1006975),
    standard_parallels=(25, 40),
    central_meridian=110,
):
    # 定义 WGS84 地理坐标系
    wgs84 = pyproj.CRS("EPSG:4326")
    # 定义兰伯特投影坐标系
    lambert_crs = pyproj.CRS(
        proj="lcc",
        lat_1=standard_parallels[0],
        lat_2=standard_parallels[1],
        lon_0=central_meridian,
        ellps="WGS84",
    )
    # 创建坐标转换器
    transformer = pyproj.Transformer.from_crs(wgs84, lambert_crs)

    # 将经纬度转换为兰伯特投影坐标
    outer_x, outer_y = transformer.transform(outer_latlon[0], outer_latlon[1])
    inner_x, inner_y = transformer.transform(inner_latlon[0], inner_latlon[1])

    # 计算投影坐标的差值（单位：米）
    delta_x_m = inner_x - outer_x
    delta_y_m = inner_y - outer_y

    # 转换为千米
    delta_x_km = delta_x_m / 1000
    delta_y_km = delta_y_m / 1000

    # 转换为网格点数偏移
    i_offset = delta_x_km / dx
    j_offset = delta_y_km / dy

    return i_offset, j_offset


def get_parent_start(we_distance, sn_distance, parent_grid_ratio, dx, dy, ref_latlon, inner_latlon):
    i_parent_start = [1]
    j_parent_start = [1]
    e_we = [int(np.ceil(we_distance[0] / dx))]
    e_sn = [int(np.ceil(sn_distance[0] / dy))]

    # top_cfg = {
    #     "cell_size": [dx * 1000, dy * 1000],  # dx, dy
    #     "center_latlon": ref_latlon,  # ref_lat, ref_lon
    #     "truelats": [25.0, 40.0],
    #     "stand_lon": 110.0,
    #     "parent_cell_size_ratio": 1,
    #     "domain_size": [195, 245],  # j, i
    #     "parent_start": [1, 1],  # j, i
    # }
    # d01 = WPSDomainLCC("d01", top_cfg)
    # domain_list = [
    #     d01,
    # ]
    for k in range(len(sn_distance) - 1):

        x = np.ceil(we_distance[k + 1] / (dx / np.prod(parent_grid_ratio[: k + 2])))
        e_we.append(
            int(
                [
                    y + 1
                    for y in [x, x + 1, x + 2, x + 3, x + 4]
                    if y % parent_grid_ratio[k + 1] == 0
                ][0]
            )
        )
        x = np.ceil(sn_distance[k + 1] / (dx / np.prod(parent_grid_ratio[: k + 2])))
        e_sn.append(
            int(
                [
                    y + 1
                    for y in [x, x + 1, x + 2, x + 3, x + 4]
                    if y % parent_grid_ratio[k + 1] == 0
                ][0]
            )
        )

        dom_dx = dx / np.prod(parent_grid_ratio[: k + 1])
        dom_dy = dy / np.prod(parent_grid_ratio[: k + 1])
        i_offset = 0
        j_offset = 0

        if k == 0:
            i_offset, j_offset = calc_grid_offset_from_latlon(
                dom_dx, dom_dy, outer_latlon=ref_latlon, inner_latlon=inner_latlon
            )
            print("offset:", i_offset, j_offset)

        i_value = int(((we_distance[k] - we_distance[k + 1]) / 2 / dom_dx + i_offset) + 1)
        j_value = int(((sn_distance[k] - sn_distance[k + 1]) / 2 / dom_dy + j_offset) + 1)

        # d0n_cfg = {
        #     'parent_cell_size_ratio': parent_grid_ratio[k + 1],
        #     'domain_size': [e_sn[k + 1], e_we[k + 1], ],
        #     'parent_start': [j_value, i_value],
        # }
        # print(f'd0{k+2}_cfg:', d0n_cfg)
        # parent = domain_list[k]
        # print('parent:', parent.dom_id)
        # d0n = WPSDomainLCC(f'd0{k + 2}', d0n_cfg, parent=parent)
        # domain_list.append(d0n)
        # print(e_sn, e_we)
        # center_latlon = d0n.ij_to_latlon((e_we[k + 1] - 1) / 2, (e_sn[k + 1] - 1) / 2, )
        # print(f'd0{k + 2} center:', center_latlon)

        # if k != 0:
        # i_offset, j_offset = calc_grid_offset_from_latlon(dom_dx, dom_dy, outer_latlon=center_latlon, inner_latlon=inner_latlon)
        # print('offset:', i_offset, j_offset)
        # i_value = round(i_value + i_offset)
        # j_value = round(j_value + j_offset)
        i_parent_start.append(i_value)
        j_parent_start.append(j_value)
    return i_parent_start, j_parent_start


def get_e_we_sn(we_distance, sn_distance, parent_grid_ratio, dx, dy):
    e_we = [int(np.ceil(we_distance[0] / dx))]
    e_sn = [int(np.ceil(sn_distance[0] / dy))]
    for k in range(len(we_distance) - 1):
        x = np.ceil(we_distance[k + 1] / (dx / np.prod(parent_grid_ratio[: k + 2])))
        e_we.append(
            int(
                [
                    y + 1
                    for y in [x, x + 1, x + 2, x + 3, x + 4]
                    if y % parent_grid_ratio[k + 1] == 0
                ][0]
            )
        )
        x = np.ceil(sn_distance[k + 1] / (dx / np.prod(parent_grid_ratio[: k + 2])))
        e_sn.append(
            int(
                [
                    y + 1
                    for y in [x, x + 1, x + 2, x + 3, x + 4]
                    if y % parent_grid_ratio[k + 1] == 0
                ][0]
            )
        )
    return e_we, e_sn


def region_geojson_to_bounds(region_geojson):
    gdf = gpd.read_file(region_geojson)
    bounds = gdf.total_bounds
    center_lon = gdf.total_bounds[0] + (gdf.total_bounds[2] - gdf.total_bounds[0]) / 2
    center_lat = gdf.total_bounds[1] + (gdf.total_bounds[3] - gdf.total_bounds[1]) / 2
    utm_zone = int(np.floor((center_lon + 180) / 6) + 1)
    utm_crs = f"+proj=utm +zone={utm_zone} +datum=WGS84 +units=m +no_defs"
    gdf_utm = gdf.to_crs(utm_crs)

    bounds = gdf_utm.bounds
    x_km = (bounds.maxx - bounds.minx)[0] / 1000
    y_km = (bounds.maxy - bounds.miny)[0] / 1000

    return x_km, y_km, center_lon, center_lat


def generate_domains(region_geojson="./370100.json", max_dom=4, dx=27, dy=27, ref_latlon=(34, 110)):
    parent_grid_ratio = [1] + [3] * (max_dom - 1)
    we_distance = [
        6615,
    ]
    sn_distance = [
        5265,
    ]

    width_km, height_km, center_lon, center_lat = region_geojson_to_bounds(region_geojson)
    width_km = width_km * 1.5
    height_km = height_km * 1.5
    we_c_distance = [width_km]
    sn_c_distance = [height_km]

    for i in range(len(parent_grid_ratio) - 2):
        we_c_distance.append((width_km * 2 ** (i + 1)))
        sn_c_distance.append((height_km * 2 ** (i + 1)))
    we_c_distance.reverse()
    sn_c_distance.reverse()
    we_distance.extend(we_c_distance)
    sn_distance.extend(sn_c_distance)

    i_parent_start, j_parent_start = get_parent_start(
        we_distance, sn_distance, parent_grid_ratio, dx, dy, ref_latlon, (center_lat, center_lon)
    )
    e_we, e_sn = get_e_we_sn(we_distance, sn_distance, parent_grid_ratio, dx, dy)
    # print('inner center:', center_lon, center_lat)
    # print(i_parent_start)
    # print(j_parent_start)
    # print(e_we)
    # print(e_sn)
    res_data = {
        "i_parent_start": ",".join(map(str, i_parent_start)),
        "j_parent_start": ",".join(map(str, j_parent_start)),
        "e_we": ",".join(map(str, e_we)),
        "e_sn": ",".join(map(str, e_sn)),
    }
    print(res_data)
    return res_data


#     template_content = f"""&geogrid
# parent_id         =    1,   1,   2,   3,
# parent_grid_ratio =    1,   3,   3,   3,
# i_parent_start    =    {i_parent_start[0]}, {i_parent_start[1]}, {i_parent_start[2]}, {i_parent_start[3]},
# j_parent_start    =    {j_parent_start[0]}, {j_parent_start[1]}, {j_parent_start[2]}, {j_parent_start[3]},
# s_we              =    1,   1,   1,   1,
# e_we              =  {e_we[0]}, {e_we[1]}, {e_we[2]}, {e_we[3]},
# s_sn              =    1,   1,   1,   1,
# e_sn              =  {e_sn[0]}, {e_sn[1]}, {e_sn[2]}, {e_sn[3]},
# geog_data_res = 'default', 'default', 'default', 'default',
# dx = 27000,
# dy = 27000,
# map_proj = 'lambert',
# ref_lat   =  34.00,
# ref_lon   =  110.00,
# truelat1  =  25.0,
# truelat2  =  40.0,
# stand_lon =  110.0,
# geog_data_path = '../WPS_GEOG/'
# /"""
# print(template_content)
# return template_content


def generate_aermap_config(
    region_geojson="./370100.json",
):
    target_epsg = 32650  # 比如 UTM Zone 50N（根据你的位置选择）
    grid_spacing = 50  # 网格分辨率（米）
    projection_id = 4  # AERMAP 投影参数，一般填 4（无旋转）

    gdf = gpd.read_file(region_geojson)

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.set_crs(epsg=4326)

    gdf_utm = gdf.to_crs(epsg=target_epsg)
    bounds = gdf_utm.total_bounds

    xmin, ymin, xmax, ymax = map(int, bounds)
    domainxy = f"{xmin} {ymin} {grid_spacing}  {xmax} {ymax} {grid_spacing}"

    xcenter = (xmin + xmax) // 2
    ycenter = (ymin + ymax) // 2
    anchorxy = f"{xcenter} {ycenter}  {xcenter} {ycenter}  {grid_spacing} {projection_id}"

    return {
        "domainxy": domainxy,
        "anchorxy": anchorxy,
    }


if __name__ == "__main__":
    # generate_domains(
    #     region_geojson=(
    #         "/mnt/vdb1/service/air-tracker-cn/server/tasks/wrf_stilt_aermod_task/utils/hebei.json"
    #     ),
    #     max_dom=3,
    #     dx=27,
    #     dy=27,
    # )

    generate_aermap_config(region_geojson=f"{os.path.dirname(__file__)}/370100.json")
