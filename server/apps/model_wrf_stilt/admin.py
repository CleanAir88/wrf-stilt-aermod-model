from django.contrib import admin
from import_export import resources
from import_export.admin import ImportExportModelAdmin

from .models import ModelWrfStilt, PollutantSource, Receptor, Region

admin.site.site_header = "MODEL-Admin"
admin.site.site_title = "MODEL-Admin"
admin.site.index_title = "MODEL-Admin"


class ReceptorResource(resources.ModelResource):
    class Meta:
        model = Receptor
        import_id_fields = ("name",)


class ReceptorAdmin(ImportExportModelAdmin):
    resource_class = ReceptorResource
    readonly_fields = ("update_time", "create_time")
    list_display = ("name", "region", "latitude", "longitude", "height")


class RegionResource(resources.ModelResource):
    class Meta:
        model = Region
        import_id_fields = ("name",)


class RegionAdmin(ImportExportModelAdmin):
    resource_class = RegionResource
    readonly_fields = ("update_time", "create_time")
    list_display = ("id", "name", "xmn", "xmx", "ymn", "ymx")


class PollutantSourceResource(resources.ModelResource):
    class Meta:
        model = PollutantSource
        import_id_fields = ("name",)


class PollutantSourceAdmin(ImportExportModelAdmin):
    resource_class = PollutantSourceResource
    readonly_fields = ("update_time", "create_time")
    list_display = (
        "name",
        "latitude",
        "longitude",
        "emis_value",
        "height",
        "diameter",
        "emission_type",
    )


class ModelWrfStiltAdmin(admin.ModelAdmin):
    readonly_fields = ("update_time", "create_time")
    list_display = ("name", "description", "xres", "yres", "n_cores", "wrf_file_retention_days")


admin.site.register(Region, RegionAdmin)
admin.site.register(Receptor, ReceptorAdmin)
admin.site.register(PollutantSource, PollutantSourceAdmin)
admin.site.register(ModelWrfStilt, ModelWrfStiltAdmin)
