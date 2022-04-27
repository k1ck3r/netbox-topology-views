from typing import Any

from dcim.models import Cable, Device, PowerFeed, PowerPanel
from django.conf import settings
from django.db.models import Q, QuerySet

IMAGE_DIR = "../../static/netbox_topology_views/img"


def get_topology_data(
    queryset: QuerySet[Device],
    hide_unconnected: bool = False,
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

    def get_id(d):
        return f"{d._meta.object_name.lower()}-{d.pk}"

    def get_object(d) -> Any:
        peer = d.get_link_peer()
        return getattr(peer, "device", getattr(peer, "power_panel", None))

    device_ids = set(get_id(d) for d in queryset)

    for qs_device in queryset:

        device_has_connections = False

        termination_query = Q(_termination_a_device_id=qs_device.pk) | Q(
            _termination_b_device_id=qs_device.pk
        )

        cables: QuerySet[Cable] = (
            Cable.objects.filter(termination_query, type="power")
            if power_only
            else Cable.objects.filter(termination_query, ~Q(type="power"))
        )

        for cable in cables:
            if (
                cable.termination_a_type.name != "circuit termination"
                and cable.termination_b_type.name != "circuit termination"
                and cable.termination_a
                and cable.termination_b
            ):
                if (
                    cable.termination_a_type.name not in ignore_cable_type
                    and cable.termination_b_type.name not in ignore_cable_type
                    and get_id(get_object(cable.termination_a)) in device_ids
                    and get_id(get_object(cable.termination_b)) in device_ids
                ):
                    device_has_connections = True

                    if cable.pk in cable_ids:
                        continue
                    cable_ids.add(cable.pk)
                    edge_ids += 1

                    cable_a_dev_name = (
                        get_object(cable.termination_a).name or "device A name unknown"
                    )
                    cable_a_name = cable.termination_a.name or "cable A name unknown"
                    cable_b_dev_name = (
                        get_object(cable.termination_b).name or "device B name unknown"
                    )
                    cable_b_name = cable.termination_b.name or "cable B name unknown"

                    edge = {
                        "id": edge_ids,
                        "from": get_id(get_object(cable.termination_a)),
                        "to": get_id(get_object(cable.termination_b)),
                        "title": f"Cable between <br> {cable_a_dev_name} [{cable_a_name}]<br>{cable_b_dev_name} [{cable_b_name}]",
                    }
                    if cable.color != "":
                        edge["color"] = f"#{cable.color}"
                    edges.append(edge)

            elif (
                settings.PLUGINS_CONFIG["netbox_topology_views"][
                    "enable_circuit_terminations"
                ]
                and cable.termination_a_type.name == "circuit termination"
                and cable.termination_a
                and cable.termination_a.circuit.pk not in circuit_ids
                and cable.termination_b
            ):

                circuit = cable.termination_a.circuit

                circuit_ids.add(circuit.pk)
                edge_ids += 1

                cable_b_dev_name = (
                    get_object(cable.termination_b).name or "device B name unknown"
                )
                cable_b_name = cable.termination_b.name or "cable B name unknown"

                edge = {}
                edge["id"] = edge_ids
                edge["to"] = get_object(cable.termination_b).pk
                edge["dashes"] = True
                title = f"Circuit provider: {circuit.provider.name}<br>Termination between <br>{cable_b_dev_name} [{cable_b_name}]<br>"

                if (
                    circuit.termination_a is not None
                    and circuit.termination_a.cable is not None
                    and circuit.termination_a.cable.pk != cable.pk
                    and circuit.termination_a.cable.termination_b is not None
                    and circuit.termination_a.get_object(cable.termination_b)
                    is not None
                ):
                    edge["from"] = circuit.termination_a.get_object(
                        cable.termination_b
                    ).pk

                    cable_a_dev_name = (
                        circuit.termination_a.get_object(cable.termination_a).name
                        or "device A name unknown"
                    )

                    cable_a_name = (
                        circuit.termination_a.cable.termination_a.name
                        or "cable A name unknown"
                    )

                    title += f"{cable_a_dev_name} [{cable_a_name}]<br>"
                    edge["title"] = title
                    edges.append(edge)

                if (
                    circuit.termination_z is not None
                    or circuit.termination_z.cable is not None
                    or circuit.termination_z.cable.pk != cable.pk
                    and circuit.termination_z.cable.termination_b is not None
                    or circuit.termination_z.get_object(cable.termination_b) is not None
                ):
                    edge["from"] = circuit.termination_z.get_object(
                        cable.termination_b
                    ).pk

                    cable_b_dev_name = (
                        circuit.termination_z.get_object(cable.termination_b).name
                        or "device B name unknown"
                    )
                    cable_b_name = (
                        circuit.termination_z.cable.termination_b.name
                        or "cable B name unknown"
                    )
                    title += f"{cable_b_dev_name} [{cable_b_name}]<br>"
                    edge["title"] = title
                    edges.append(edge)

        if qs_device.pk in nodes_ids:
            continue

        if not hide_unconnected or (hide_unconnected and device_has_connections):
            nodes_ids.add(get_id(qs_device))

            dev_name = qs_device.name or "device name unknown"
            node_content = ""

            if isinstance(qs_device, Device):
                if qs_device.device_type is not None:
                    node_content += f"<tr><th>Type: </th><td>{qs_device.device_type.model}</td></tr>"
                if qs_device.device_role.name is not None:
                    node_content += (
                        f"<tr><th>Role: </th><td>{qs_device.device_role.name}</td></tr>"
                    )
                if qs_device.serial != "":
                    node_content += (
                        f"<tr><th>Serial: </th><td>{qs_device.serial}</td></tr>"
                    )
                if qs_device.primary_ip is not None:
                    node_content += f"<tr><th>IP Address: </th><td>{qs_device.primary_ip.address}</td></tr>"

            dev_title = f"<table> {node_content} </table>"

            node = {}
            node["id"] = get_id(qs_device)
            node["name"] = dev_name
            node["label"] = dev_name
            node["title"] = dev_title
            node["shape"] = "image"

            if isinstance(qs_device, Device):
                node["href"] = f"/dcim/devices/{qs_device.pk}"
            elif isinstance(qs_device, PowerFeed):
                node["href"] = f"/dcim/power-feeds/{qs_device.pk}"
            elif isinstance(qs_device, PowerPanel):
                node["href"] = f"/dcim/power-panels/{qs_device.pk}"
            else:
                node["href"] = None

            if (
                hasattr(qs_device, "device_role")
                and qs_device.device_role.slug
                in settings.PLUGINS_CONFIG["netbox_topology_views"]["device_img"]
            ):
                node["image"] = f"{IMAGE_DIR}/{qs_device.device_role.slug}.png"
            else:
                node["image"] = f"{IMAGE_DIR}/role-unknown.png"

            if hasattr(qs_device, "device_role") and qs_device.device_role.color != "":
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
