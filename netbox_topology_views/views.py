from dcim.models import DeviceRole
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import render
from django.views.generic import View
from extras.models import Tag

from .forms import DeviceFilterForm


class TopologyHomeView(PermissionRequiredMixin, View):
    permission_required = ("dcim.view_site", "dcim.view_device")

    """
    Show the home page
    """

    def get(self, request):

        if not request.GET:
            preselected_device_roles = settings.PLUGINS_CONFIG["netbox_topology_views"][
                "preselected_device_roles"
            ]
            preselected_tags = settings.PLUGINS_CONFIG["netbox_topology_views"][
                "preselected_tags"
            ]

            q_device_role_id = DeviceRole.objects.filter(
                name__in=preselected_device_roles
            ).values_list("id", flat=True)
            q_tags = Tag.objects.filter(name__in=preselected_tags).values_list(
                "name", flat=True
            )

            q = QueryDict(mutable=True)
            q.setlist("device_role_id", list(q_device_role_id))
            q.setlist("tag", list(q_tags))
            q["draw_init"] = settings.PLUGINS_CONFIG["netbox_topology_views"][
                "draw_default_layout"
            ]
            query_string = q.urlencode()
            return HttpResponseRedirect(f"{request.path}?{query_string}")

        return render(
            request,
            "netbox_topology_views/index.html.j2",
            {"filter_form": DeviceFilterForm(request.GET, label_suffix="")},
        )
