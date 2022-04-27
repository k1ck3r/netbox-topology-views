from typing import Any

from dcim.models import Device, PowerFeed, PowerPanel
from django.conf import settings
from netbox_topology_views.api.utils import get_topology_data
from netbox_topology_views.filters import DeviceFilterSet
from rest_framework.response import Response
from rest_framework.routers import APIRootView
from rest_framework.viewsets import ReadOnlyModelViewSet

from .serializers import TopologyDummySerializer


class TopologyViewsRootView(APIRootView):
    def get_view_name(self):
        return "TopologyViews"


class SaveCoordsViewSet(ReadOnlyModelViewSet):
    queryset = Device.objects.all()
    serializer_class = TopologyDummySerializer

    def patch(self, request):
        results = {}
        if settings.PLUGINS_CONFIG["netbox_topology_views"]["allow_coordinates_saving"]:
            device_id = None
            x_coord = None
            y_coord = None
            if "node_id" in request.data:
                if request.data["node_id"]:
                    device_id = request.data["node_id"]
            if "x" in request.data:
                if request.data["x"]:
                    x_coord = request.data["x"]
            if "y" in request.data:
                if request.data["y"]:
                    y_coord = request.data["y"]

            actual_device = Device.objects.get(id=device_id)

            if "coordinates" in actual_device.custom_field_data:
                actual_device.custom_field_data["coordinates"] = "%s;%s" % (
                    x_coord,
                    y_coord,
                )
                actual_device.save()
                results["status"] = "saved coords"
            else:
                try:
                    actual_device.custom_field_data["coordinates"] = "%s;%s" % (
                        x_coord,
                        y_coord,
                    )
                    actual_device.save()
                    results["status"] = "saved coords"
                except:
                    results["status"] = "coords custom field not created"
                    return Response(status=500)

            return Response(results)
        else:
            results["status"] = "not allowed to save coords"
            return Response(results, status=500)


class TopologyDataViewSet(ReadOnlyModelViewSet):
    queryset = Device.objects.all()
    serializer_class = TopologyDummySerializer

    def list(self, request):
        self.queryset: Any = [
            *DeviceFilterSet(request.GET, self.queryset).qs,
            # *PowerFeed.objects.all(),
            *PowerPanel.objects.all(),
        ]

        power_only = request.GET.get("power_only", "").lower() == "true"
        hide_unconnected = request.GET.get("hide_unconnected") == "on"

        return Response(get_topology_data(self.queryset, hide_unconnected, power_only))
