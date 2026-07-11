from flask import Blueprint, request, jsonify
import switch_manager

api_blueprint = Blueprint("api", __name__, url_prefix="/api")


def _not_connected_response():
    return jsonify({"success": False, "error": "Not connected to switch"}), 400


@api_blueprint.route("/connect", methods=["POST"])
def api_connect():
    data = request.get_json() or {}
    ip = data.get("ip", "")
    port = int(data.get("port", 22))
    username = data.get("username", "")
    password = data.get("password", "")

    success, message = switch_manager.connect_to_switch(ip, port, username, password)
    return jsonify({"success": success, "message": message})


@api_blueprint.route("/disconnect", methods=["POST"])
def api_disconnect():
    switch_manager.disconnect_switch()
    return jsonify({"success": True, "message": "Disconnected"})


@api_blueprint.route("/status", methods=["GET"])
def api_status():
    return jsonify({"connected": switch_manager.is_connected()})


@api_blueprint.route("/ports", methods=["GET"])
def api_get_ports():
    if not switch_manager.is_connected():
        return _not_connected_response()

    ports = switch_manager.get_all_ports()
    return jsonify({"success": True, "ports": ports})


@api_blueprint.route("/port/<port_name>", methods=["GET"])
def api_get_port(port_name):
    if not switch_manager.is_connected():
        return _not_connected_response()

    port_name = port_name.replace("-", "/")

    port_info = switch_manager.get_port_info(port_name)
    mac_list = switch_manager.get_mac_table(port_name)

    port_info["mac_addresses"] = mac_list
    return jsonify({"success": True, "port": port_info})


@api_blueprint.route("/port/<port_name>/enable", methods=["POST"])
def api_enable_port(port_name):
    if not switch_manager.is_connected():
        return _not_connected_response()

    port_name = port_name.replace("-", "/")
    success = switch_manager.enable_port(port_name)
    return jsonify({"success": success})


@api_blueprint.route("/port/<port_name>/disable", methods=["POST"])
def api_disable_port(port_name):
    if not switch_manager.is_connected():
        return _not_connected_response()

    port_name = port_name.replace("-", "/")
    success = switch_manager.disable_port(port_name)
    return jsonify({"success": success})


@api_blueprint.route("/port/<port_name>/reload", methods=["POST"])
def api_reload_port(port_name):
    if not switch_manager.is_connected():
        return _not_connected_response()

    port_name = port_name.replace("-", "/")
    success = switch_manager.reload_port(port_name)
    return jsonify({"success": success})


@api_blueprint.route("/port/<port_name>/reset", methods=["POST"])
def api_reset_port(port_name):
    if not switch_manager.is_connected():
        return _not_connected_response()

    port_name = port_name.replace("-", "/")
    success = switch_manager.reset_port(port_name)
    return jsonify({"success": success})


@api_blueprint.route("/port/<port_name>/config", methods=["PUT"])
def api_config_port(port_name):
    if not switch_manager.is_connected():
        return _not_connected_response()

    port_name = port_name.replace("-", "/")
    data = request.get_json() or {}

    results = {}

    if "description" in data:
        results["description"] = switch_manager.set_port_description(
            port_name, data["description"]
        )

    if "vlan_id" in data or "mode" in data:
        results["vlan"] = switch_manager.set_port_vlan(
            port_name,
            data.get("vlan_id", "1"),
            data.get("mode", "access"),
            data.get("native_vlan"),
        )

    if "speed" in data:
        results["speed"] = switch_manager.set_port_speed(port_name, data["speed"])

    if "duplex" in data:
        results["duplex"] = switch_manager.set_port_duplex(port_name, data["duplex"])

    if "port_security" in data:
        results["port_security"] = switch_manager.set_port_security(
            port_name,
            data["port_security"],
            data.get("max_mac", 1),
            data.get("sticky_mac", False),
        )

    overall_success = len(results) > 0 and all(results.values())
    return jsonify({"success": overall_success, "results": results})
