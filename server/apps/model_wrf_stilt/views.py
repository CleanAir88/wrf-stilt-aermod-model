import pendulum
from celery import current_app
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from loguru import logger
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from tasks.wrf_stilt_aermod_task.utils import create_domains
from utils import utils_netcdf

from .models import (
    EmissionContributionData,
    ModelWrfStilt,
    PollutantSource,
    Receptor,
    Region,
)
from .serializers import (
    EmissionContributionDataSerializer,
    ModelWRFStiltSerializer,
    PollutantSourceSerializer,
    ReceptorSerializer,
    RegionSerializer,
)
from .tasks import run_wrf_stilt_task


class TaskCreationSerializer(serializers.Serializer):
    run_date = serializers.DateTimeField(
        input_formats=["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"],
        required=True,
    )
    receptor_ids = serializers.CharField(required=False, default=None)
    run_wrf = serializers.BooleanField(required=False, default=True)
    run_stilt = serializers.BooleanField(required=False, default=True)
    run_aermod = serializers.BooleanField(required=False, default=True)


class ModelWRFStiltViewSet(viewsets.ModelViewSet):
    queryset = ModelWrfStilt.objects.all()
    serializer_class = ModelWRFStiltSerializer
    permission_classes = []
    authentication_classes = []

    @action(detail=False, methods=["get"])
    def create_task(self, request):

        serializer = TaskCreationSerializer(data=request.query_params)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400)
        validated_data = serializer.validated_data
        logger.info(validated_data)

        inspect = current_app.control.inspect()
        worker_dict = inspect.active()
        queue_length = -1
        for worker_name, task_list in worker_dict.items():
            if "wrf_stilt_worker" in worker_name:
                queue_length = len(task_list)
        if queue_length > 10:
            return JsonResponse(
                {
                    "error": (
                        "Task queue is full. Please try again later. Current task count:"
                        f" {queue_length}"
                    )
                },
                status=400,
            )

        _task = run_wrf_stilt_task.delay(
            run_date=validated_data["run_date"].strftime("%Y-%m-%d %H:%M:%S+00:00"),
            wrf=validated_data["run_wrf"],
            stilt=validated_data["run_stilt"],
            receptor_ids=validated_data["receptor_ids"],
            aermod=validated_data["run_aermod"],
        )
        return JsonResponse({
            "message": "Task created, please wait for completion",
            "task_id": _task.id,
            "task_params": validated_data,
            "worker_status": worker_dict,
        })

    @action(detail=False, methods=["post"])
    def calc_domains(self, request):
        """
        Calculate the grid of the region
        """
        # try:
        max_dom = int(request.data.get("max_dom"))
        geojson_file = request.FILES.get("geojson")
        grid_data = create_domains.generate_domains(
            region_geojson=geojson_file, max_dom=max_dom, dx=27, dy=27, ref_latlon=(34, 110)
        )
        return JsonResponse(grid_data, safe=False)
        # except Exception as e:
        #     logger.error(e)
        #     return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["get"])
    def get_stilt_data(self, request):
        """
        Get STILT model data for a specific receptor
        """
        try:
            time = request.query_params.get("time")
            receptor_id = request.query_params.get("receptor_id")
            resp_type = request.query_params.get("resp_type")
            if not all([time, receptor_id]):
                return JsonResponse(
                    {"error": "Missing required parameters: time and receptor_id"}, status=400
                )

            receptor = Receptor.objects.get(id=receptor_id)
            lng = receptor.longitude
            lat = receptor.latitude
            height = receptor.height
            file = utils_netcdf.parse_file_name(time=time, lng=lng, lat=lat, hight=int(height))
            data = utils_netcdf.get_nc_data(file)
            lng = [row[0] for row in data["data"]]
            lat = [row[1] for row in data["data"]]
            data["bounds"] = [[min(lat), min(lng)], [max(lat), max(lng)]]

            if resp_type == "png":
                buffer = utils_netcdf.stilt_to_png(data)
                return HttpResponse(buffer.getvalue(), content_type="image/png")
            else:
                return JsonResponse(data)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

    @action(detail=False, methods=["get"])
    def get_stilt_merge_data(self, request):
        """
        Get merged STILT data for a specific receptor over multiple time periods
        """
        st = request.query_params.get("st")
        et = request.query_params.get("et")
        receptor_id = request.query_params.get("receptor_id")
        resp_type = request.query_params.get("resp_type")
        if not all([st, et, receptor_id]):
            return JsonResponse(
                {"error": "Missing required parameters: st, et, receptor_id"}, status=400
            )
        st = pendulum.from_format(st, "YYYYMMDDHHmm")
        et = pendulum.from_format(et, "YYYYMMDDHHmm")

        if receptor_id:
            receptor = Receptor.objects.get(id=receptor_id)
            lng = receptor.longitude
            lat = receptor.latitude
            height = int(receptor.height)

        all_data = []
        all_data_dict = {}
        columns = []
        not_exist_files = []
        while st < et:
            tm_str = st.format("YYYYMMDDHHmm")[:-2] + "00"
            try:
                file = utils_netcdf.parse_file_name(time=tm_str, lng=lng, lat=lat, hight=height)
                data = utils_netcdf.get_nc_data(file)
                value_data = data["data"]
                columns = data["columns"]
                for i in value_data:
                    grid_key = f"{i[0]}:{i[1]}"
                    all_data_dict.setdefault(grid_key, []).append(i[2])
                st = st.add(hours=1)
            except Exception as e:
                logger.error(e)
                not_exist_files.append(tm_str)
                st = st.add(hours=1)
                continue

        for k in all_data_dict:
            [lng, lat] = k.split(":")
            avg_val = sum(all_data_dict[k]) / len(all_data_dict[k])
            all_data.append([float(lng), float(lat), avg_val])
        data = {"columns": columns, "data": all_data}
        lng = [row[0] for row in data["data"]]
        lat = [row[1] for row in data["data"]]
        data["bounds"] = [[min(lat), min(lng)], [max(lat), max(lng)]]

        if resp_type == "png":
            buffer = utils_netcdf.stilt_to_png(data)
            return HttpResponse(buffer.getvalue(), content_type="image/png")
        else:
            return JsonResponse(data)

    @action(detail=False, methods=["get"])
    def get_emission_contribution(self, request):
        """
        Get emission contribution data for a specific receptor
        """
        receptor_id = request.query_params.get("receptor_id")
        time = request.query_params.get("time")
        dist = request.query_params.get("dist", 5000)
        if not receptor_id:
            return JsonResponse({"error": "Missing required parameter: receptor_id"}, status=400)

        try:
            # 获取污染贡献数据，需要显示关联的污染源信息
            queryset = (
                EmissionContributionData.objects.filter(receptor=receptor_id, time=time)
                .filter(dist__lte=dist)
                .select_related("receptor", "pollutant_source")
            )
            serializer = EmissionContributionDataSerializer(queryset, many=True)
            data = serializer.data
            return JsonResponse(list(data), safe=False)
        except Exception as e:
            logger.error(e)
            return JsonResponse({"error": str(e)}, status=500)


class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.all()
    serializer_class = RegionSerializer


class ReceptorViewSet(viewsets.ModelViewSet):
    queryset = Receptor.objects.all()
    serializer_class = ReceptorSerializer
    permission_classes = []
    authentication_classes = []

    @action(detail=False, methods=["post"])
    def bulk_import(self, request):
        """
        Bulk import Receptor: delete all and import new data.
        Data format: [{{...}}, {{...}}]
        """
        data = request.data

        if not isinstance(data, list):
            return JsonResponse({"error": "Data should be a list of objects."}, status=400)
        print(data)
        serializer = ReceptorSerializer(data=data, many=True)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400, safe=False)
        try:
            with transaction.atomic():
                Receptor.objects.all().delete()
                serializer.save()
            return JsonResponse({"message": "Import successful", "count": len(data)})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


class PollutantSourceViewSet(viewsets.ModelViewSet):
    queryset = PollutantSource.objects.all()
    serializer_class = PollutantSourceSerializer
    permission_classes = []
    authentication_classes = []

    @action(detail=False, methods=["post"])
    def bulk_import(self, request):
        """
        Bulk import PollutantSource: delete all and import new data.
        Data format: [{{...}}, {{...}}]
        """
        data = request.data
        if not isinstance(data, list):
            return JsonResponse({"error": "Data should be a list of objects."}, status=400)

        serializer = PollutantSourceSerializer(data=data, many=True)
        if not serializer.is_valid():
            return JsonResponse(serializer.errors, status=400, safe=False)
        try:
            with transaction.atomic():
                PollutantSource.objects.all().delete()
                serializer.save()
            return JsonResponse({"message": "Import successful", "count": len(data)})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)


"""
--- Example: Import Receptor or PollutantSource ---

# POST /api/model_wrf_stilt/receptor/bulk_import/  (or /pollutantsource/bulk_import/)
# Content-Type: application/json
# Body:
# [
#   {"name": "R1", "longitude": 120.1, "latitude": 30.2, "height": 10},
#   {"name": "R2", "longitude": 120.2, "latitude": 30.3, "height": 20}
# ]

# Response:
# {"message": "Import successful", "count": 2}
"""


@csrf_exempt
def tool_page_view(request):
    if request.method == "POST":
        max_dom = request.POST.get("max_dom")
        file = request.FILES.get("file")

        if not max_dom or not file:
            return render(request, "tool_page.html", {"error": "Parameters or files are missing"})

        result = create_domains.generate_domains(
            region_geojson=file, max_dom=int(max_dom), dx=27, dy=27, ref_latlon=(34, 110)
        )
        result_aermap = create_domains.generate_aermap_config(region_geojson=file)
        return render(request, "tool_page.html", {"result": result, "result_aermap": result_aermap})
    return render(request, "tool_page.html")
