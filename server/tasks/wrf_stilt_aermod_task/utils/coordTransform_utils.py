# -*- coding: utf-8 -*-

import math
from math import asin, cos, radians, sin, sqrt

from pyproj import Transformer

x_pi = 3.14159265358979324 * 3000.0 / 180.0
pi = 3.1415926535897932384626  # π
a = 6378245.0  # 长半轴
ee = 0.00669342162296594323  # 扁率


def round6(x):
    return round(x, 6)


def gcj02_to_bd09(lng, lat):
    """
    火星坐标系(GCJ-02)转百度坐标系(BD-09)
    谷歌、高德——>百度
    :param lng:火星坐标经度
    :param lat:火星坐标纬度
    :return:
    """
    z = math.sqrt(lng * lng + lat * lat) + 0.00002 * math.sin(lat * x_pi)
    theta = math.atan2(lat, lng) + 0.000003 * math.cos(lng * x_pi)
    bd_lng = z * math.cos(theta) + 0.0065
    bd_lat = z * math.sin(theta) + 0.006
    return round6(bd_lng), round6(bd_lat)


def gcj02tobd09(lng, lat):
    return gcj02_to_bd09(lng, lat)


def bd09_to_gcj02(bd_lon, bd_lat):
    """
    百度坐标系(BD-09)转火星坐标系(GCJ-02)
    百度——>谷歌、高德
    :param bd_lat:百度坐标纬度
    :param bd_lon:百度坐标经度
    :return:转换后的坐标列表形式
    """
    x = bd_lon - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * x_pi)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * x_pi)
    gg_lng = z * math.cos(theta)
    gg_lat = z * math.sin(theta)
    return round6(gg_lng), round6(gg_lat)


def bd09togcj02(bd_lon, bd_lat):
    return bd09_to_gcj02(bd_lon, bd_lat)


def wgs84_to_gcj02(lng, lat):
    """
    WGS84转GCJ02(火星坐标系)
    :param lng:WGS84坐标系的经度
    :param lat:WGS84坐标系的纬度
    :return:
    """
    if out_of_china(lng, lat):  # 判断是否在国内
        return lng, lat
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return round6(mglng), round6(mglat)


def wgs84togcj02(lng, lat):
    return wgs84_to_gcj02(lng, lat)


def gcj02_to_wgs84(lng, lat):
    """
    GCJ02(火星坐标系)转GPS84
    :param lng:火星坐标系的经度
    :param lat:火星坐标系纬度
    :return:
    """
    if out_of_china(lng, lat):
        return lng, lat
    dlat = _transformlat(lng - 105.0, lat - 35.0)
    dlng = _transformlng(lng - 105.0, lat - 35.0)
    radlat = lat / 180.0 * pi
    magic = math.sin(radlat)
    magic = 1 - ee * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((a * (1 - ee)) / (magic * sqrtmagic) * pi)
    dlng = (dlng * 180.0) / (a / sqrtmagic * math.cos(radlat) * pi)
    mglat = lat + dlat
    mglng = lng + dlng
    return round6(lng * 2 - mglng), round6(lat * 2 - mglat)


def gcj02towgs84(lng, lat):
    return gcj02_to_wgs84(lng, lat)


def bd09_to_wgs84(bd_lon, bd_lat):
    lon, lat = bd09_to_gcj02(bd_lon, bd_lat)
    return gcj02_to_wgs84(lon, lat)


def bd09towgs84(bd_lon, bd_lat):
    return bd09_to_wgs84(bd_lon, bd_lat)


def wgs84_to_bd09(lon, lat):
    lon, lat = wgs84_to_gcj02(lon, lat)
    return gcj02_to_bd09(lon, lat)


def wgs84tobd09(lon, lat):
    return wgs84_to_bd09(lon, lat)


def _transformlat(lng, lat):
    ret = (
        -100.0
        + 2.0 * lng
        + 3.0 * lat
        + 0.2 * lat * lat
        + 0.1 * lng * lat
        + 0.2 * math.sqrt(math.fabs(lng))
    )
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lat * pi) + 40.0 * math.sin(lat / 3.0 * pi)) * 2.0 / 3.0
    ret += (160.0 * math.sin(lat / 12.0 * pi) + 320 * math.sin(lat * pi / 30.0)) * 2.0 / 3.0
    return ret


def _transformlng(lng, lat):
    ret = (
        300.0
        + lng
        + 2.0 * lat
        + 0.1 * lng * lng
        + 0.1 * lng * lat
        + 0.1 * math.sqrt(math.fabs(lng))
    )
    ret += (20.0 * math.sin(6.0 * lng * pi) + 20.0 * math.sin(2.0 * lng * pi)) * 2.0 / 3.0
    ret += (20.0 * math.sin(lng * pi) + 40.0 * math.sin(lng / 3.0 * pi)) * 2.0 / 3.0
    ret += (150.0 * math.sin(lng / 12.0 * pi) + 300.0 * math.sin(lng / 30.0 * pi)) * 2.0 / 3.0
    return ret


def transformlat(lng, lat):
    return _transformlat(lng, lat)


def transformlng(lng, lat):
    return _transformlng(lng, lat)


def out_of_china(lng, lat):
    """
    判断是否在国内，不在国内不做偏移
    :param lng:
    :param lat:
    :return:
    """
    return not (lng > 73.66 and lng < 135.05 and lat > 3.86 and lat < 53.55)


def geodistance(lng1, lat1, lng2, lat2):
    # lng1,lat1,lng2,lat2 = (120.12802999999997,30.28708,115.86572000000001,28.7427)
    lng1, lat1, lng2, lat2 = map(
        radians, [float(lng1), float(lat1), float(lng2), float(lat2)]
    )  # 经纬度转换成弧度
    dlon = lng2 - lng1
    dlat = lat2 - lat1
    a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
    distance = 2 * asin(sqrt(a)) * 6371 * 1000  # 地球平均半径，6371km
    distance = round(distance, 3)
    return distance


def wgs84toUTMZone50(lng, lat):
    # 定义WGS84坐标系和UTM Zone 50坐标系
    wgs84 = "epsg:4326"  # WGS84坐标系
    utm50 = "epsg:32650"  # UTM Zone 50坐标系

    # 使用Transformer进行转换
    transformer = Transformer.from_crs(wgs84, utm50)
    x, y = transformer.transform(lat, lng)  # 注意可能的轴顺序变化
    return x, y


def UTMZone50toWgs84(x, y):
    # 定义WGS84坐标系和UTM Zone 50坐标系
    wgs84 = "epsg:4326"  # WGS84坐标系
    utm50 = "epsg:32650"  # UTM Zone 50坐标系

    # 使用Transformer进行转换
    transformer = Transformer.from_crs(utm50, wgs84)
    x, y = transformer.transform(x, y)  # 注意可能的轴顺序变化
    return x, y


def calc_point_distance(point1, point2):
    """
    计算两个经纬度点之间的距离（米）
    :param point1: 第一个点的坐标 (经度, 纬度)
    :param point2: 第二个点的坐标 (经度, 纬度)
    :return: 两点之间的距离，单位为米
    """
    import math

    # 地球平均半径，单位为米
    R = 6371000

    # 将经纬度转换为弧度
    lng1, lat1 = math.radians(point1[0]), math.radians(point1[1])
    lng2, lat2 = math.radians(point2[0]), math.radians(point2[1])

    # 经纬度差值
    dlng = lng2 - lng1
    dlat = lat2 - lat1

    # Haversine 公式
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c

    return round(distance)


if __name__ == "__main__":
    print(UTMZone50toWgs84(408496, 3870144))
    print(UTMZone50toWgs84(585373, 4105903))
    print(UTMZone50toWgs84(509337, 4112287))

    print(wgs84toUTMZone50(116.226064, 35.990622))
    print(wgs84toUTMZone50(117.975331, 37.532886))

    print(wgs84toUTMZone50(116, 36))
    print(wgs84toUTMZone50(118, 38))
