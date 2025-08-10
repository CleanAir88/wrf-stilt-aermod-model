from rest_framework import serializers

from .models import (
    EmissionContributionData,
    ModelWrfStilt,
    PollutantSource,
    Receptor,
    Region,
)


class RegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = "__all__"


class SimpleRegionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Region
        fields = ["id", "name", "xmn", "xmx", "ymn", "ymx"]


class ReceptorSerializer(serializers.ModelSerializer):
    region = SimpleRegionSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        source="region", queryset=Region.objects.all(), write_only=True  # 指定写入目标字段
    )

    class Meta:
        model = Receptor
        fields = "__all__"


class PollutantSourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = PollutantSource
        fields = "__all__"


class ModelWRFStiltSerializer(serializers.ModelSerializer):

    class Meta:
        model = ModelWrfStilt
        fields = "__all__"


class EmissionContributionDataSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmissionContributionData
        fields = "__all__"
        read_only_fields = ["id", "created_at", "updated_at"]
        extra_kwargs = {
            "run_date": {"input_formats": ["%Y-%m-%d", "%Y-%m-%d %H:%M:%S"]},
        }
        depth = 1
