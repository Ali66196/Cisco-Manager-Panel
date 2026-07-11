import re
import time
from netmiko import ConnectHandler
from netmiko.exceptions import AuthenticationException, NetMikoTimeoutException


ssh_connection = None


def connect_to_switch(ip, port, username, password):
    global ssh_connection

    device = {
        "device_type": "cisco_ios",
        "host": ip,
        "port": port,
        "username": username,
        "password": password,
        "timeout": 10,
    }

    try:
        ssh_connection = ConnectHandler(**device)
        return True, "Connection successful"
    except AuthenticationException:
        return False, "Authentication failed: wrong username or password"
    except NetMikoTimeoutException:
        return False, "Connection timed out: switch unreachable"
    except Exception as e:
        return False, str(e)


def disconnect_switch():
    global ssh_connection
    try:
        if ssh_connection is not None:
            ssh_connection.disconnect()
    except Exception:
        pass
    finally:
        ssh_connection = None


def is_connected():
    return ssh_connection is not None


def run_command(command):
    if not is_connected():
        return None
    try:
        return ssh_connection.send_command(command)
    except Exception:
        return None


def run_config_commands(commands):
    if not is_connected():
        return False
    try:
        ssh_connection.send_config_set(commands)
        ssh_connection.send_command("write memory")
        return True
    except Exception:
        return False


def _parse_interfaces_status_line(line):
    pattern = re.compile(
        r"^((?:Fa|Gi|Te|Eth)\S+)"
        r"\s+"
        r"(\S.*?)?"
        r"\s{2,}"
        r"(connected|notconnect|disabled|err-disabled|inactive)"
        r"\s+"
        r"(\S+)"
        r"\s+"
        r"(\S+)"
        r"\s+"
        r"(\S+)"
    )

    m = pattern.match(line)
    if not m:
        pattern2 = re.compile(
            r"^((?:Fa|Gi|Te|Eth)\S+)"
            r"\s+"
            r"(connected|notconnect|disabled|err-disabled|inactive)"
            r"\s+"
            r"(\S+)"
            r"\s+"
            r"(\S+)"
            r"\s+"
            r"(\S+)"
        )
        m2 = pattern2.match(line)
        if not m2:
            return None
        port_name  = m2.group(1)
        status_raw = m2.group(2)
        vlan_col   = m2.group(3)
        duplex     = m2.group(4)
        speed      = m2.group(5)
        description = ""
    else:
        port_name   = m.group(1)
        description = (m.group(2) or "").strip()
        status_raw  = m.group(3)
        vlan_col    = m.group(4)
        duplex      = m.group(5)
        speed       = m.group(6)

    if status_raw == "connected":
        status = "up"
    elif status_raw == "disabled":
        status = "disabled"
    else:
        status = "down"

    if vlan_col.lower() == "trunk":
        mode = "trunk"
        vlan = "1"
    else:
        mode = "access"
        vlan = vlan_col

    return {
        "port_name":   port_name,
        "status":      status,
        "vlan":        vlan,
        "mode":        mode,
        "duplex":      duplex,
        "speed":       speed,
        "description": description,
    }


def get_all_ports():
    if not is_connected():
        return []

    output = run_command("show interfaces status")
    if not output:
        return []

    ports = []
    index = 1

    for line in output.splitlines():
        line = line.strip()
        if not re.match(r"^(?:Fa|Gi|Te|Eth)", line):
            continue

        parsed = _parse_interfaces_status_line(line)
        if not parsed:
            continue

        ports.append({
            "name":        parsed["port_name"],
            "index":       index,
            "status":      parsed["status"],
            "vlan":        parsed["vlan"],
            "speed":       parsed["speed"],
            "duplex":      parsed["duplex"],
            "mode":        parsed["mode"],
            "description": parsed["description"],
            "type":        detect_port_type(parsed["port_name"]),
        })

        index += 1
        if index > 16:
            break

    return ports


def get_port_info(port_name):
    if not is_connected():
        return {}

    output_if = run_command(f"show interfaces {port_name}") or ""
    output_cfg = run_command(f"show running-config interface {port_name}") or ""

    if "is administratively down" in output_if:
        status = "disabled"
    elif "is up" in output_if:
        status = "up"
    else:
        status = "down"

    desc_match = re.search(r'description (.+)', output_cfg)
    description = desc_match.group(1).strip() if desc_match else ""

    vlan_match = re.search(r'switchport access vlan (\d+)', output_cfg)
    vlan = vlan_match.group(1) if vlan_match else "1"

    if "switchport mode trunk" in output_cfg:
        mode = "trunk"
    else:
        mode = "access"

    speed_match = re.search(r'^\s+speed (\w+)', output_cfg, re.MULTILINE)
    speed = speed_match.group(1) if speed_match else "auto"

    duplex_match = re.search(r'^\s+duplex (\w+)', output_cfg, re.MULTILINE)
    duplex = duplex_match.group(1) if duplex_match else "auto"

    port_security = "switchport port-security" in output_cfg

    max_mac_match = re.search(r'switchport port-security maximum (\d+)', output_cfg)
    max_mac = int(max_mac_match.group(1)) if max_mac_match else 1

    return {
        "name":          port_name,
        "status":        status,
        "description":   description,
        "vlan":          vlan,
        "mode":          mode,
        "speed":         speed,
        "duplex":        duplex,
        "port_security": port_security,
        "max_mac":       max_mac,
        "type":          detect_port_type(port_name),
    }


def detect_port_type(port_name):
    if port_name.startswith("Fa"):
        return "FastEthernet"
    elif port_name.startswith("Gi"):
        return "GigabitEthernet"
    elif port_name.startswith("Te"):
        return "TenGigabitEthernet"
    else:
        return "Ethernet"


def enable_port(port_name):
    return run_config_commands([
        f"interface {port_name}",
        "no shutdown",
    ])


def disable_port(port_name):
    return run_config_commands([
        f"interface {port_name}",
        "shutdown",
    ])


def reload_port(port_name):
    try:
        run_config_commands([f"interface {port_name}", "shutdown"])
        time.sleep(2)
        run_config_commands([f"interface {port_name}", "no shutdown"])
        return True
    except Exception:
        return False


def set_port_description(port_name, description):
    return run_config_commands([
        f"interface {port_name}",
        f"description {description}",
    ])


def set_port_vlan(port_name, vlan_id, mode, native_vlan=None):
    commands = [f"interface {port_name}"]

    if mode == "access":
        commands.append("switchport mode access")
        commands.append(f"switchport access vlan {vlan_id}")
    elif mode == "trunk":
        commands.append("switchport mode trunk")
        if native_vlan:
            commands.append(f"switchport trunk native vlan {native_vlan}")

    return run_config_commands(commands)


def set_port_speed(port_name, speed):
    return run_config_commands([
        f"interface {port_name}",
        f"speed {speed}",
    ])


def set_port_duplex(port_name, duplex):
    return run_config_commands([
        f"interface {port_name}",
        f"duplex {duplex}",
    ])


def set_port_security(port_name, enabled, max_mac=1, sticky=False):
    commands = [f"interface {port_name}"]

    if enabled:
        commands.append("switchport port-security")
        commands.append(f"switchport port-security maximum {max_mac}")
        if sticky:
            commands.append("switchport port-security mac-address sticky")
        commands.append("switchport port-security violation restrict")
    else:
        commands.append("no switchport port-security")

    return run_config_commands(commands)


def reset_port(port_name):
    return run_config_commands([
        f"interface {port_name}",
        "no description",
        "no shutdown",
        "switchport mode access",
        "switchport access vlan 1",
        "no speed",
        "no duplex",
        "no switchport port-security",
    ])


def get_mac_table(port_name):
    if not is_connected():
        return []

    output = run_command(f"show mac address-table interface {port_name}")
    if not output:
        return []

    macs = re.findall(r'([0-9a-fA-F]{4}\.[0-9a-fA-F]{4}\.[0-9a-fA-F]{4})', output)
    return macs
