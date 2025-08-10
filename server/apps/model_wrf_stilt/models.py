from django.core.validators import RegexValidator
from django.db import models
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from utils.model import BaseModel

name_validator = RegexValidator(
    regex=r"^[a-zA-Z]+$", message="只允许使用大小写英文字母", code="letters_only"
)


def fixed_aermap_path(instance, filename):
    return "aermap_data/aermap_data.tif"


class ModelWrfStilt(BaseModel):
    """WRF-STILT模型"""

    DATA_SOURCE_CHOICES = [
        ("fnl", "fnl"),
        ("gfs", "gfs"),
    ]

    name = models.CharField(max_length=100, verbose_name=_("模型名称"), validators=[name_validator])
    description = models.TextField(blank=True, null=True, verbose_name=_("描述信息"))
    max_dom = models.IntegerField(verbose_name=_("嵌套域数"), default=4)
    stilt_wrf_dom = models.IntegerField(verbose_name=_("计算STILT的WRF域数"), default=3)
    dx = models.IntegerField(verbose_name=_("dx(m)"), default=27000)
    dy = models.IntegerField(verbose_name=_("dy(m)"), default=27000)
    interval_seconds = models.IntegerField(verbose_name=_("时间间隔(秒)"), default=21600)
    xres = models.FloatField(verbose_name=_("X方向分辨率"), default=0.001)
    yres = models.FloatField(verbose_name=_("Y方向分辨率"), default=0.001)
    n_cores = models.IntegerField(verbose_name=_("计算核心数"), default=8)
    wrf_file_retention_days = models.IntegerField(verbose_name=_("WRF文件保留天数"), default=365)
    i_parent_start = models.CharField(max_length=100, verbose_name=_("i_parent_start"))
    j_parent_start = models.CharField(max_length=100, verbose_name=_("j_parent_start"))
    e_we = models.CharField(max_length=100, verbose_name=_("e_we"))
    e_sn = models.CharField(max_length=100, verbose_name=_("e_sn"))
    obsgrid_enabled = models.BooleanField(default=False, verbose_name=_("是否启用obsgrid"))
    obsdata_url_config = models.JSONField(
        blank=True, null=True, verbose_name=_("obsgrid地面站请求URL配置")
    )
    data_source = models.CharField(
        max_length=100, verbose_name=_("数据源"), choices=DATA_SOURCE_CHOICES, default="gfs"
    )
    # https://daejeon-kreonet-net.nationalresearchplatform.org:8443/ncar/rda/d351000/little_r/2025/OBS:2025062912
    obsgrid_upper_air_url = models.URLField(
        verbose_name=_("obsgrid高空大气数据源URL"),
        default="https://daejeon-kreonet-net.nationalresearchplatform.org:8443/ncar/rda/d351000/little_r/",
        null=True,
        blank=True,
        help_text=_("设置为空则不启用obsgrid高空大气数据"),
    )

    fnl_url = models.URLField(
        verbose_name=_("fnl数据源URL"),
        default="https://data.rda.ucar.edu/d083002/grib2/",
    )
    gfs_url = models.URLField(
        verbose_name=_("gfs数据源URL"),
        default="https://nomads.ncep.noaa.gov/pub/data/nccf/com/gfs/prod/",
    )
    data_delay_hours = models.IntegerField(verbose_name=_("延迟小时数"), default=0)

    aermap_datafile = models.FileField(
        upload_to=fixed_aermap_path,
        verbose_name=_("AERMAP数据文件tif"),
        null=True,
        blank=True,
        help_text=_("上传AERMAP数据文件tif"),
    )
    aermod_domainxy = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_("example: 430399 3983176 50 587613 4154016 50"),
    )
    aermod_anchorxy = models.CharField(
        max_length=200,
        null=True,
        blank=True,
        help_text=_("example: 509006 4068596 509006 4068596 50 4"),
    )

    class Meta:
        verbose_name = _("WRF-STILT模型")
        verbose_name_plural = _("WRF-STILT模型管理")
        db_table = "w_model_config"

    def __str__(self):
        return self.name


class Region(BaseModel):
    name = models.CharField(max_length=100, unique=True, verbose_name=_("区域名称"))
    xmn = models.FloatField(verbose_name=_("最小经度"))
    xmx = models.FloatField(verbose_name=_("最大经度"))
    ymn = models.FloatField(verbose_name=_("最小纬度"))
    ymx = models.FloatField(verbose_name=_("最大纬度"))
    geojson = models.TextField(verbose_name=_("区域边界 GeoJSON"), null=True, blank=True)

    class Meta:
        verbose_name = _("区域")
        verbose_name_plural = _("区域管理")
        db_table = "w_region"

    def __str__(self):
        return self.name


class Receptor(BaseModel):
    """受体模型"""

    name = models.CharField(max_length=100, verbose_name=_("受体名称"))
    latitude = models.FloatField(verbose_name=_("纬度"))
    longitude = models.FloatField(verbose_name=_("经度"))
    height = models.FloatField(verbose_name=_("高度（米）"))
    region = models.ForeignKey(
        Region,
        on_delete=models.CASCADE,
        related_name="receptors",
        verbose_name=_("所属区域"),
    )
    description = models.TextField(blank=True, null=True, verbose_name=_("备注"))

    class Meta:
        verbose_name = _("受体")
        verbose_name_plural = _("受体管理")
        db_table = "w_receptor"

    def __str__(self):
        return self.name


class PollutantSource(BaseModel):
    """污染源模型"""

    name = models.CharField(max_length=100, verbose_name=_("污染源名称"))
    emission_type = models.CharField(
        max_length=50,
        verbose_name=_("污染源类别"),
        default="其他",
        choices=[
            ("电力生产", _("电力生产")),
            ("电力热力源其他", _("电力热力源其他")),
            ("工业源", _("工业源")),
            ("移动源", _("移动源")),
            ("油品储运销", _("油品储运销")),
            ("生活源", _("生活源")),
            ("农业源", _("农业源")),
            ("扬尘源", _("扬尘源")),
            ("废弃物处理源", _("废弃物处理源")),
            ("生物质开放燃烧源", _("生物质开放燃烧源")),
            ("其他", _("其他")),
        ],
    )
    time_type = models.CharField(
        max_length=50,
        verbose_name=_("时间类型"),
        choices=[
            ("hourly", _("小时")),
            ("yearly", _("年")),
        ],
        default="yearly",
    )
    latitude = models.FloatField(verbose_name=_("纬度"), null=True, blank=True)
    longitude = models.FloatField(verbose_name=_("经度"), null=True, blank=True)
    emis_value = models.FloatField(verbose_name=_("污染源排放量(t)"), null=True, blank=True)
    height = models.FloatField(verbose_name=_("烟囱高度(m)"), null=True, blank=True, default=45.0)
    diameter = models.FloatField(verbose_name=_("烟囱内径(m)"), null=True, blank=True, default=1.0)
    stack_temp = models.FloatField(
        verbose_name=_("排气温度(K)"),
        null=True,
        blank=True,
        default=400.0,
    )
    exit_velocity = models.FloatField(
        verbose_name=_("排气速度(m/s)"),
        null=True,
        blank=True,
        default=10.0,
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("污染源")
        verbose_name_plural = _("污染源管理")
        db_table = "w_pollutant_source"


# 污染源与受体点的贡献数据
class EmissionContributionData(BaseModel):
    """污染源对受体点的贡献数据"""

    pollutant_source = models.ForeignKey(
        PollutantSource,
        on_delete=models.CASCADE,
        related_name="contribution_data",
        verbose_name=_("污染源ID"),
    )
    receptor = models.ForeignKey(
        Receptor,
        on_delete=models.CASCADE,
        related_name="contribution_data",
        verbose_name=_("受体点ID"),
    )
    time = models.DateTimeField(default=now, verbose_name=_("时间"))
    emis_value = models.FloatField(verbose_name=_("贡献值"), default=0.0)
    emis_rate = models.FloatField(verbose_name=_("贡献占比%"), default=0.0)

    emis_value_s = models.FloatField(verbose_name=_("敏感性贡献值"), default=0.0)
    emis_rate_s = models.FloatField(verbose_name=_("敏感性贡献占比%"), default=0.0)
    dist = models.FloatField(verbose_name=_("距离"), null=True, blank=True)

    class Meta:
        verbose_name = _("污染源贡献数据")
        verbose_name_plural = _("污染源贡献数据管理")
        db_table = "w_emission_contribution_data"
