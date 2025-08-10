from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    ModelWRFStiltViewSet,
    PollutantSourceViewSet,
    ReceptorViewSet,
    RegionViewSet,
    tool_page_view,
)

router = DefaultRouter()
router.register(r"model_wrf_stilt", ModelWRFStiltViewSet)
router.register(r"region", RegionViewSet)
router.register(r"receptor", ReceptorViewSet)
router.register(r"pollutant_source", PollutantSourceViewSet)

urlpatterns = router.urls
urlpatterns += [
    path("tool/", tool_page_view, name="tool_page"),
]
