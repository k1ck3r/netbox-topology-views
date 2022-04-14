import json
from typing import Optional

from dcim.models import Cable, Device, DeviceRole
from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.db.models import Q, QuerySet
from django.http import HttpResponseRedirect, QueryDict
from django.shortcuts import render
from django.views.generic import View
from extras.models import Tag

from .filters import DeviceFilterSet
from .forms import DeviceFilterForm


def get_topology_data(
    queryset: QuerySet[Device],
    hide_unconnected: Optional[bool] = None,
    power_only: bool = False,
):
    nodes = []
    nodes_ids = set()
    edges = []
    edge_ids = 0
    cable_ids = set()
    circuit_ids = set()
    if not queryset:
        return None

    ignore_cable_type = settings.PLUGINS_CONFIG["netbox_topology_views"][
        "ignore_cable_type"
    ]

    device_ids = [d.pk for d in queryset]

    for qs_device in queryset:
        device_has_connections = False

        cables = Cable.objects.filter(
            Q(_termination_a_device_id=qs_device.pk)
            | Q(_termination_b_device_id=qs_device.pk)
        )
        for cable in cables:
            if (
                cable.termination_a_type.name != "circuit termination"
                and cable.termination_b_type.name != "circuit termination"
            ):
                if (
                    cable.termination_a_type.name not in ignore_cable_type
                    and cable.termination_b_type.name not in ignore_cable_type
                ):
                    print(cable.type)
                    if not hasattr(cable.termination_b, "device"):
                        # TODO: Power feeds should be treated as a device

                        pass
                    elif cable.type != "power" and power_only:
                        pass
                    elif cable.pk not in cable_ids:
                        if (
                            cable.termination_a.device.pk in device_ids
                            and cable.termination_b.device.pk in device_ids
                        ):
                            device_has_connections = True
                            cable_ids.add(cable.pk)
                            edge_ids += 1
                            cable_a_dev_name = (
                                cable.termination_a.device.name
                                or "device A name unknown"
                            )
                            cable_a_name = (
                                cable.termination_a.name or "cable A name unknown"
                            )
                            cable_b_dev_name = (
                                cable.termination_b.device.name
                                or "device B name unknown"
                            )
                            cable_b_name = (
                                cable.termination_b.name or "cable B name unknown"
                            )

                            edge = {
                                "id": edge_ids,
                                "from": cable.termination_a.device.pk,
                                "to": cable.termination_b.device.pk,
                                "title": f"Cable between <br> {cable_a_dev_name} [{cable_a_name}]<br>{cable_b_dev_name} [{cable_b_name}]",
                            }
                            if cable.color != "":
                                edge["color"] = f"#{cable.color}"
                            edges.append(edge)
                    else:
                        if (
                            cable.termination_a.device.pk in device_ids
                            and cable.termination_b.device.pk in device_ids
                        ):
                            device_has_connections = True
                    continue

            # if settings.PLUGINS_CONFIG["netbox_topology_views"][
            #     "enable_circuit_terminations"
            # ]:
            #     if link_from.termination_a_type.name == "circuit termination":
            #         if link_from.termination_a.circuit.pk not in circuit_ids:
            #             circuit_ids.add(link_from.termination_a.circuit.pk)
            #             edge_ids += 1

            #             cable_b_dev_name = link_from.termination_b.device.name
            #             if cable_b_dev_name is None:
            #                 cable_b_dev_name = "device B name unknown"
            #             cable_b_name = link_from.termination_b.name
            #             if cable_b_name is None:
            #                 cable_b_name = "cable B name unknown"

            #             edge = {}
            #             edge["id"] = edge_ids
            #             edge["to"] = link_from.termination_b.device.pk
            #             edge["dashes"] = True
            #             title = f"Circuit provider: {link_from.termination_a.circuit.provider.name}<br>Termination between <br>{cable_b_dev_name} [{cable_b_name}]<br>"

            #             if (
            #                 link_from.termination_a.circuit.termination_a is not None
            #                 and link_from.termination_a.circuit.termination_a.cable
            #                 is not None
            #                 and link_from.termination_a.circuit.termination_a.cable.pk
            #                 != link_from.pk
            #                 and link_from.termination_a.circuit.termination_a.cable.termination_b
            #                 is not None
            #                 and link_from.termination_a.circuit.termination_a.cable.termination_b.device
            #                 is not None
            #             ):
            #                 edge[
            #                     "from"
            #                 ] = (
            #                     link_from.termination_a.circuit.termination_a.cable.termination_b.device.pk
            #                 )

            #                 cable_a_dev_name = (
            #                     link_from.termination_a.circuit.termination_a.cable.termination_b.device.name
            #                 )
            #                 if cable_a_dev_name is None:
            #                     cable_a_dev_name = "device B name unknown"
            #                 cable_b_name = (
            #                     link_from.termination_a.circuit.termination_a.cable.termination_b.name
            #                 )
            #                 if cable_a_name is None:
            #                     cable_a_name = "cable B name unknown"
            #                 title += f"{cable_a_dev_name} [{cable_a_name}]<br>"
            #                 edge["title"] = title
            #                 edges.append(edge)

            #             if (
            #                 link_from.termination_a.circuit.termination_z is None
            #                 or link_from.termination_a.circuit.termination_z.cable
            #                 is None
            #                 or link_from.termination_a.circuit.termination_z.cable.pk
            #                 != link_from.pk
            #                 and link_from.termination_a.circuit.termination_z.cable.termination_b
            #                 is None
            #                 or link_from.termination_a.circuit.termination_z.cable.termination_b.device
            #                 is None
            #             ):
            #                 continue

            #             edge[
            #                 "from"
            #             ] = (
            #                 link_from.termination_a.circuit.termination_z.cable.termination_b.device.pk
            #             )

            #             cable_a_dev_name = (
            #                 link_from.termination_a.circuit.termination_z.cable.termination_b.device.name
            #             )
            #             if cable_a_dev_name is None:
            #                 cable_a_dev_name = "device B name unknown"
            #             cable_a_name = (
            #                 link_from.termination_a.circuit.termination_z.cable.termination_b.name
            #             )
            #             if cable_a_name is None:
            #                 cable_a_name = "cable B name unknown"
            #             title += f"{cable_a_dev_name} [{cable_a_name}]<br>"
            #             edge["title"] = title
            #             edges.append(edge)

        if qs_device.pk in nodes_ids:
            continue

        if hide_unconnected == None or (
            hide_unconnected is True and device_has_connections is True
        ):
            nodes_ids.add(qs_device.pk)

            dev_name = qs_device.name
            if dev_name is None:
                dev_name = "device name unknown"

            node_content = ""

            if qs_device.device_type is not None:
                node_content += (
                    f"<tr><th>Type: </th><td>{qs_device.device_type.model}</td></tr>"
                )
            if qs_device.device_role.name is not None:
                node_content += (
                    f"<tr><th>Role: </th><td>{qs_device.device_role.name}</td></tr>"
                )
            if qs_device.serial != "":
                node_content += f"<tr><th>Serial: </th><td>{qs_device.serial}</td></tr>"
            if qs_device.primary_ip is not None:
                node_content += f"<tr><th>IP Address: </th><td>{qs_device.primary_ip.address}</td></tr>"

            dev_title = "<table> %s </table>" % (node_content)

            node = {}
            node["id"] = qs_device.pk
            node["name"] = dev_name
            node["label"] = dev_name
            node["title"] = dev_title
            node["shape"] = "image"
            if (
                qs_device.device_role.slug
                in settings.PLUGINS_CONFIG["netbox_topology_views"]["device_img"]
            ):
                node[
                    "image"
                ] = f"../../static/netbox_topology_views/img/{qs_device.device_role.slug}.png"
            else:
                node[
                    "image"
                ] = "../../static/netbox_topology_views/img/role-unknown.png"

            if qs_device.device_role.color != "":
                node["color.border"] = f"#{qs_device.device_role.color}"

            if (
                "coordinates" in qs_device.custom_field_data
                and qs_device.custom_field_data["coordinates"] is not None
                and ";" in qs_device.custom_field_data["coordinates"]
            ):
                cords = qs_device.custom_field_data["coordinates"].split(";")
                node["x"] = int(cords[0])
                node["y"] = int(cords[1])
                node["physics"] = False
            nodes.append(node)

    return {"nodes": nodes, "edges": edges}


class TopologyHomeView(PermissionRequiredMixin, View):
    permission_required = ("dcim.view_site", "dcim.view_device")

    """
    Show the home page
    """

    def get(self, request):
        self.filterset = DeviceFilterSet
        self.queryset = Device.objects.all()
        self.queryset = self.filterset(request.GET, self.queryset).qs
        topo_data = None

        if request.GET:
            hide_unconnected = None
            if "hide_unconnected" in request.GET:
                if request.GET["hide_unconnected"] == "on":
                    hide_unconnected = True

            if "draw_init" in request.GET:
                if request.GET["draw_init"].lower() == "true":
                    topo_data = get_topology_data(self.queryset, hide_unconnected)
            else:
                topo_data = get_topology_data(self.queryset, hide_unconnected)
        else:
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
            {
                "filter_form": DeviceFilterForm(request.GET, label_suffix=""),
                "topology_data": json.dumps(topo_data),
            },
        )


class TopologyPowerView(PermissionRequiredMixin, View):
    permission_required = ("dcim.view_site", "dcim.view_device")

    """
    Show the power page
    """

    def get(self, request):
        self.filterset = DeviceFilterSet
        self.queryset = Device.objects.all()
        self.queryset = self.filterset(request.GET, self.queryset).qs

        topo_data = get_topology_data(
            self.queryset,
            request.GET.get("hide_unconnected", "on") == "on" if request.GET else True,
            True,
        )

        return render(
            request,
            "netbox_topology_views/power.html.j2",
            {
                "filter_form": DeviceFilterForm(request.GET, label_suffix=""),
                "topology_data": json.dumps(topo_data),
            },
        )
