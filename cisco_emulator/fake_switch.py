#!/usr/bin/env python3
"""
شبیه‌ساز SSH سوییچ Cisco IOS — سرور mock برای تست Netmiko
"""

import re
import socket
import sys
import threading

import paramiko

# ─── تنظیمات SSH ─────────────────────────────────────────────────────────────
HOST = "127.0.0.1"
PORT = 2222
SSH_USERNAME = "cisco"
SSH_PASSWORD = "cisco123"

# قفل برای دسترسی thread-safe به state
_state_lock = threading.Lock()

# وضعیت شبیه‌ساز — تمام اطلاعات پورت‌ها اینجا ذخیره می‌شوند
SWITCH_STATE = {
    "hostname": "Switch",
    "ports": {
        "Fa0/1": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "PC-Accounting",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/2": {
            "status": "connected",
            "vlan": "10",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "PC-IT",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/3": {
            "status": "connected",
            "vlan": "20",
            "speed": "10",
            "duplex": "a-half",
            "mode": "access",
            "description": "IP-Camera-01",
            "shutdown": False,
            "port_security": True,
            "max_mac": 1,
            "sticky": True,
        },
        "Fa0/4": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/5": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "trunk",
            "description": "Uplink-to-Core",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/6": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/7": {
            "status": "connected",
            "vlan": "30",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "Printer",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/8": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/9": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/10": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/11": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "DISABLED-PORT",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/12": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/13": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/14": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/15": {
            "status": "connected",
            "vlan": "1",
            "speed": "100",
            "duplex": "a-full",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
        "Fa0/16": {
            "status": "notconnect",
            "vlan": "1",
            "speed": "auto",
            "duplex": "auto",
            "mode": "access",
            "description": "",
            "shutdown": False,
            "port_security": False,
            "max_mac": 1,
            "sticky": False,
        },
    },
    # MAC addressهای فیک برای پورت‌های متصل
    "mac_table": {
        "Fa0/1": ["0050.7966.6800"],
        "Fa0/2": ["0050.7966.6801", "0050.7966.6802"],
        "Fa0/3": ["aabb.cc00.0100"],
        "Fa0/4": [],
        "Fa0/5": ["0050.7966.6810"],
    },
}

# وضعیت فیزیکی لینک (بدون در نظر گرفتن shutdown اداری)
INITIAL_LINK_STATUS = {
    port: ("notconnect" if p["shutdown"] else p["status"])
    for port, p in SWITCH_STATE["ports"].items()
}

# آدرس MAC فیک برای هر پورت (برای show interface)
PORT_MAC_ADDRESSES = {
    f"Fa0/{i}": f"0001.6c2e.f3{i:02x}" for i in range(1, 17)
}

WELCOME_BANNER = (
    "Cisco IOS Software, Version 12.2(55)SE12, RELEASE SOFTWARE (fc2)\r\n"
    "Technical Support: http://www.cisco.com/techsupport\r\n"
    "Copyright (c) 1986-2018 by Cisco Systems, Inc.\r\n"
    "\r\n"
    "Switch>enable\r\n"
)

INVALID_INPUT = "% Invalid input detected at '^' marker.\r\n"


def normalize_port(name: str) -> str | None:
    """تبدیل نام پورت به فرم استاندارد Fa0/X"""
    name = name.strip()
    # FastEthernet0/1 → Fa0/1
    m = re.match(r"(?i)(?:fa(?:stethernet)?|fastethernet)(\d+)/(\d+)$", name)
    if m:
        return f"Fa{m.group(1)}/{m.group(2)}"
    m = re.match(r"(?i)^fa(\d+)/(\d+)$", name)
    if m:
        return f"Fa{m.group(1)}/{m.group(2)}"
    return None


def long_port_name(short: str) -> str:
    """Fa0/1 → FastEthernet0/1"""
    m = re.match(r"Fa(\d+)/(\d+)", short)
    if m:
        return f"FastEthernet{m.group(1)}/{m.group(2)}"
    return short


def duplex_display(duplex: str) -> str:
    """نمایش duplex در show interface"""
    mapping = {
        "a-full": "Full-duplex",
        "a-half": "Half-duplex",
        "full": "Full-duplex",
        "half": "Half-duplex",
        "auto": "Auto-duplex",
    }
    return mapping.get(duplex, duplex)


def speed_display(speed: str) -> str:
    """نمایش speed در show interface"""
    if speed == "auto":
        return "Auto-speed"
    if speed == "10":
        return "10Mb/s"
    if speed == "100":
        return "100Mb/s"
    if speed == "1000":
        return "1000Mb/s"
    return f"{speed}Mb/s"


def config_duplex_value(duplex: str) -> str:
    """تبدیل duplex داخلی به مقدار config"""
    if duplex in ("a-full", "full"):
        return "full"
    if duplex in ("a-half", "half"):
        return "half"
    return duplex


# ─── تولید خروجی دستورات show ───────────────────────────────────────────────


def show_interfaces_status() -> str:
    """خروجی show interfaces status"""
    lines = [
        "Port      Name               Status       Vlan       Duplex  Speed Type",
    ]
    with _state_lock:
        for port_name in sorted(
            SWITCH_STATE["ports"].keys(),
            key=lambda p: int(p.split("/")[1]),
        ):
            p = SWITCH_STATE["ports"][port_name]
            vlan_col = "trunk" if p["mode"] == "trunk" else p["vlan"]
            name = p["description"][:19]
            line = (
                f"{port_name:<10}"
                f"{name:<19}"
                f"{p['status']:<13}"
                f"{vlan_col:<11}"
                f"{p['duplex']:<8}"
                f"{p['speed']:<6}"
                f"10/100BaseTX"
            )
            lines.append(line)
    return "\r\n".join(lines) + "\r\n"


def show_interface_detail(port: str) -> str:
    """خروجی show interface Fa0/X"""
    long_name = long_port_name(port)
    with _state_lock:
        if port not in SWITCH_STATE["ports"]:
            return INVALID_INPUT
        p = SWITCH_STATE["ports"][port]
        mac = PORT_MAC_ADDRESSES.get(port, "0000.0000.0000")

        if p["shutdown"]:
            status_line = f"{long_name} is administratively down, line protocol is down"
        elif p["status"] == "notconnect":
            status_line = (
                f"{long_name} is down, line protocol is down (notconnect)"
            )
        elif p["status"] == "disabled":
            status_line = (
                f"{long_name} is administratively down, line protocol is down"
            )
        else:
            status_line = (
                f"{long_name} is up, line protocol is up (connected)"
            )

        desc_line = ""
        if p["description"]:
            desc_line = f"  Description: {p['description']}\r\n"

        speed_to_bw = {
            "10": "10000",
            "100": "100000",
            "1000": "1000000",
            "auto": "100000",
        }

        bw = speed_to_bw.get(p["speed"], "100000")
        duplex_str = duplex_display(p["duplex"])
        speed_str = speed_display(p["speed"])

    output = (
        f"{status_line}\r\n"
        f"  Hardware is Fast Ethernet, address is {mac} (bia {mac})\r\n"
        f"{desc_line}"
        f"  MTU 1500 bytes, BW {bw} Kbit/sec, DLY 100 usec,\r\n"
        f"     reliability 255/255, txload 1/255, rxload 1/255\r\n"
        f"  Encapsulation ARPA, loopback not set\r\n"
        f"  Keepalive set (10 sec)\r\n"
        f"  {duplex_str}, {speed_str}, media type is 10/100BaseTX\r\n"
        f"  input flow-control is off, output flow-control is unsupported\r\n"
        f"  ARP type: ARPA, ARP Timeout 04:00:00\r\n"
        f"  Last input 00:00:01, output 00:00:02, output hang never\r\n"
        f"  Last clearing of \"show interface\" counters never\r\n"
        f"  Input queue: 0/75/0/0 (size/max/drops/flushes); "
        f"Total output drops: 0\r\n"
        f"  Queueing strategy: fifo\r\n"
        f"  Output queue: 0/40 (size/max)\r\n"
        f"  5 minute input rate 0 bits/sec, 0 packets/sec\r\n"
        f"  5 minute output rate 0 bits/sec, 0 packets/sec\r\n"
        f"     0 packets input, 0 bytes, 0 no buffer\r\n"
        f"     0 input errors, 0 CRC, 0 frame, 0 overrun, 0 ignored\r\n"
        f"     0 watchdog, 0 multicast, 0 pause input\r\n"
        f"     0 input packets with dribble condition detected\r\n"
        f"     0 packets output, 0 bytes, 0 underruns\r\n"
        f"     0 output errors, 0 collisions, 0 interface resets\r\n"
        f"     0 unknown protocol drops\r\n"
        f"     0 babbles, 0 late collision, 0 deferred\r\n"
        f"     0 lost carrier, 0 no carrier, 0 pause output\r\n"
        f"     0 output buffer failures, 0 output buffers swapped out\r\n"
    )
    return output


def show_running_config_interface(port: str) -> str:
    """خروجی show running-config interface Fa0/X"""
    with _state_lock:
        if port not in SWITCH_STATE["ports"]:
            return INVALID_INPUT
        p = SWITCH_STATE["ports"][port]

        lines = [
            "Building configuration...",
            "",
            "Current configuration : 93 bytes",
            "!",
            f"interface {long_port_name(port)}",
        ]

        if p["description"]:
            lines.append(f" description {p['description']}")

        if p["mode"] == "access":
            lines.append(f" switchport access vlan {p['vlan']}")
            lines.append(" switchport mode access")
        elif p["mode"] == "trunk":
            lines.append(" switchport mode trunk")
            lines.append(f" switchport trunk native vlan {p['vlan']}")

        if p["speed"] != "auto":
            lines.append(f" speed {p['speed']}")
        if p["duplex"] != "auto":
            lines.append(f" duplex {config_duplex_value(p['duplex'])}")

        if p["port_security"]:
            lines.append(" switchport port-security")
            if p["max_mac"] > 1:
                lines.append(
                    f" switchport port-security maximum {p['max_mac']}"
                )
            if p["sticky"]:
                lines.append(
                    " switchport port-security mac-address sticky"
                )

        if p["shutdown"]:
            lines.append(" shutdown")

        # spanning-tree portfast برای پورت‌های access متصل
        if p["mode"] == "access" and not p["shutdown"]:
            lines.append(" spanning-tree portfast")

        lines.append("end")

    return "\r\n".join(lines) + "\r\n"


def show_mac_address_table_interface(port: str) -> str:
    """خروجی show mac address-table interface Fa0/X"""
    with _state_lock:
        if port not in SWITCH_STATE["ports"]:
            return INVALID_INPUT
        p = SWITCH_STATE["ports"][port]
        macs = SWITCH_STATE["mac_table"].get(port, [])
        vlan = p["vlan"]

    header = (
        "          Mac Address Table\r\n"
        "-------------------------------------------\r\n"
        "\r\n"
        "Vlan    Mac Address       Type        Ports\r\n"
        "----    -----------       --------    -----\r\n"
    )

    rows = []
    for mac in macs:
        rows.append(f"   {vlan:<3} {mac:<17} DYNAMIC     {port}")

    body = "\r\n".join(rows)
    if body:
        body += "\r\n"

    footer = (
        f"\r\nTotal Mac Addresses for this criterion: {len(macs)}\r\n"
    )
    return header + body + footer


def write_memory_response() -> str:
    """خروجی write memory / copy running-config startup-config"""
    return "Building configuration...\r\n[OK]\r\n"


# ─── پردازش دستورات config ─────────────────────────────────────────────────


def apply_interface_command(port: str, cmd: str) -> bool:
    """
    اعمال دستور config روی پورت — True اگر موفق، False اگر نامعتبر
    """
    cmd = cmd.strip()
    if not cmd:
        return True

    with _state_lock:
        if port not in SWITCH_STATE["ports"]:
            return False
        p = SWITCH_STATE["ports"][port]

        if cmd == "shutdown":
            p["shutdown"] = True
            p["status"] = "disabled"
            return True

        if cmd == "no shutdown":
            p["shutdown"] = False
            if p["status"] == "disabled":
                p["status"] = INITIAL_LINK_STATUS[port]
            return True

        if cmd == "switchport mode access":
            p["mode"] = "access"
            return True

        if cmd == "switchport mode trunk":
            p["mode"] = "trunk"
            return True

        m = re.match(r"switchport access vlan (\d+)", cmd)
        if m:
            p["vlan"] = m.group(1)
            return True

        m = re.match(r"switchport trunk native vlan (\d+)", cmd)
        if m:
            p["vlan"] = m.group(1)
            return True

        m = re.fullmatch(r"speed\s+(1000|100|10|auto)", cmd)
        if m:
            p["speed"] = m.group(1)
            return True

        m = re.match(r"duplex (auto|full|half)", cmd)
        if m:
            val = m.group(1)
            if val == "full":
                p["duplex"] = "a-full"
            elif val == "half":
                p["duplex"] = "a-half"
            else:
                p["duplex"] = "auto"
            return True

        if cmd == "switchport port-security":
            p["port_security"] = True
            return True

        if cmd == "no switchport port-security":
            p["port_security"] = False
            return True

        m = re.match(r"switchport port-security maximum (\d+)", cmd)
        if m:
            p["max_mac"] = int(m.group(1))
            return True

        if cmd == "switchport port-security mac-address sticky":
            p["sticky"] = True
            return True

        if cmd == "switchport port-security violation restrict":
            return True

        if cmd == "no description":
            p["description"] = ""
            return True

        if cmd == "no speed":
            p["speed"] = "auto"
            return True

        if cmd == "no duplex":
            p["duplex"] = "auto"
            return True

        m = re.match(r"description (.+)", cmd)
        if m:
            p["description"] = m.group(1)
            return True

    return False


# ─── session handler ─────────────────────────────────────────────────────────


class CiscoSSHServer(paramiko.ServerInterface):
    """احراز هویت SSH"""

    def check_auth_password(self, username, password):
        if username == SSH_USERNAME and password == SSH_PASSWORD:
            return paramiko.AUTH_SUCCESSFUL
        return paramiko.AUTH_FAILED

    def check_channel_request(self, kind, chanid):
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_shell_request(self, channel):
        return True

    def check_channel_pty_request(
        self, channel, term, width, height, pixelwidth, pixelheight, modes
    ):
        return True

    def get_allowed_auths(self, username):
        return "password"


class CiscoSession:
    """مدیریت یک session SSH — parse دستورات و prompt"""

    def __init__(self, channel):
        self.channel = channel
        # mode: enable | config | interface
        self.current_mode = "enable"
        self.current_interface = None
        self._buffer = ""

    def prompt(self) -> str:
        """برگرداندن prompt فعلی"""
        hostname = SWITCH_STATE["hostname"]
        if self.current_mode == "config":
            return f"{hostname}(config)#"
        if self.current_mode == "interface":
            return f"{hostname}(config-if)#"
        return f"{hostname}#"

    def send(self, text: str):
        """ارسال متن به client"""
        self.channel.send(text)

    def send_line(self, text: str = ""):
        """ارسال خط با CRLF"""
        self.channel.send(text + "\r\n")

    def process_command(self, cmd: str) -> str:
        """پردازش یک دستور و برگرداندن خروجی (بدون prompt)"""
        cmd = cmd.strip()
        if not cmd:
            return ""

        cmd_lower = cmd.lower()

        # دستورات terminal — Netmiko در session_preparation ارسال می‌کند
        if re.match(r"terminal (width|length) \d+", cmd_lower):
            return ""

        # ── دستورات global در هر mode ──
        if cmd_lower == "end":
            self.current_mode = "enable"
            self.current_interface = None
            return ""

        # ── enable mode ──
        if self.current_mode == "enable":
            return self._process_enable(cmd, cmd_lower)

        # ── config mode ──
        if self.current_mode == "config":
            return self._process_config(cmd, cmd_lower)

        # ── interface mode ──
        if self.current_mode == "interface":
            return self._process_interface(cmd, cmd_lower)

        return INVALID_INPUT

    def _process_enable(self, cmd: str, cmd_lower: str) -> str:
        """دستورات در حالت privileged"""
        if cmd_lower == "enable":
            return ""

        if cmd_lower in ("configure terminal", "conf t", "config t"):
            self.current_mode = "config"
            return ""

        if cmd_lower in ("write memory", "copy running-config startup-config"):
            return write_memory_response()

        if cmd_lower == "show interfaces status":
            return show_interfaces_status()

        # show interface Fa0/X
        m = re.match(
            r"show interface(?:s)? (?:(?:interface )?)"
            r"(.+)$",
            cmd,
            re.IGNORECASE,
        )
        if m:
            port = normalize_port(m.group(1))
            if port:
                return show_interface_detail(port)
            return INVALID_INPUT

        # show running-config interface Fa0/X
        m = re.match(
            r"show running-config interface (.+)$",
            cmd,
            re.IGNORECASE,
        )
        if m:
            port = normalize_port(m.group(1))
            if port:
                return show_running_config_interface(port)
            return INVALID_INPUT

        # show mac address-table interface Fa0/X
        m = re.match(
            r"show mac address-table interface (.+)$",
            cmd,
            re.IGNORECASE,
        )
        if m:
            port = normalize_port(m.group(1))
            if port:
                return show_mac_address_table_interface(port)
            return INVALID_INPUT

        return INVALID_INPUT

    def _process_config(self, cmd: str, cmd_lower: str) -> str:
        """دستورات در config mode"""
        if cmd_lower == "exit":
            self.current_mode = "enable"
            return ""

        # interface Fa0/X
        m = re.match(r"interface (.+)$", cmd, re.IGNORECASE)
        if m:
            port = normalize_port(m.group(1))
            if port and port in SWITCH_STATE["ports"]:
                self.current_mode = "interface"
                self.current_interface = port
                return ""
            return INVALID_INPUT

        return INVALID_INPUT

    def _process_interface(self, cmd: str, cmd_lower: str) -> str:
        """دستورات در interface config mode"""
        if cmd_lower == "exit":
            self.current_mode = "config"
            self.current_interface = None
            return ""

        if apply_interface_command(self.current_interface, cmd):
            return ""

        return INVALID_INPUT

    def run(self):
        """حلقه اصلی session"""
        self.send(WELCOME_BANNER)
        self.send(self.prompt())

        while self.channel.active:
            try:
                data = self.channel.recv(4096)
            except Exception:
                break

            if not data:
                break

            self._buffer += data.decode("utf-8", errors="replace")

            # پردازش خطوط کامل
            while "\n" in self._buffer or "\r" in self._buffer:
                # جدا کردن اولین خط
                for sep in ("\r\n", "\n", "\r"):
                    if sep in self._buffer:
                        line, self._buffer = self._buffer.split(sep, 1)
                        break
                else:
                    break

                # echo کاراکترها — Netmiko معمولاً echo خودش را دارد
                # دستور را parse کن (خط ممکن است شامل echo باشد)
                cmd = line.strip()

                # نادیده گرفتن خطوط control
                if not cmd:
                    self.send_line()
                    self.send(self.prompt())
                    continue

                # حذف echo prompt اگر وجود داشت
                prompt_pattern = re.compile(
                    r"^(Switch(?:\(config(?:-if)?\))?[#>])\s*",
                    re.IGNORECASE,
                )
                cmd = prompt_pattern.sub("", cmd).strip()

                if not cmd:
                    self.send_line()
                    self.send(self.prompt())
                    continue

                output = self.process_command(cmd)

                # echo دستور برای سازگاری با Netmiko
                self.send_line(cmd)

                if output:
                    # خروجی از قبل CRLF دارد
                    if not output.endswith("\r\n"):
                        output += "\r\n"
                    self.send(output)

                self.send(self.prompt())


def handle_client(client_sock, addr):
    """handle کردن یک client در thread جداگانه"""
    transport = None
    try:
        transport = paramiko.Transport(client_sock)
        transport.add_server_key(HOST_KEY)
        transport.start_server(server=CiscoSSHServer())

        channel = transport.accept(timeout=20)
        if channel is None:
            return

        session = CiscoSession(channel)
        session.run()

    except Exception as exc:
        print(f"[!] Error handling client {addr[0]}: {exc}", file=sys.stderr)
    finally:
        if transport:
            transport.close()
        client_sock.close()
        print(f"[*] Client disconnected: {addr[0]}")


def main():
    """راه‌اندازی SSH server"""
    global HOST_KEY
    HOST_KEY = paramiko.RSAKey.generate(2048)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((HOST, PORT))
    sock.listen(100)

    print("[*] Cisco Switch Emulator started", flush=True)
    print(f"[*] Listening on {HOST}:{PORT}", flush=True)
    print(f"[*] SSH Username: {SSH_USERNAME}", flush=True)
    print(f"[*] SSH Password: {SSH_PASSWORD}", flush=True)
    print("[*] Simulating 16 FastEthernet ports (Fa0/1 - Fa0/16)", flush=True)
    print("[*] Press Ctrl+C to stop", flush=True)

    try:
        while True:
            client_sock, addr = sock.accept()
            thread = threading.Thread(
                target=handle_client,
                args=(client_sock, addr),
                daemon=True,
            )
            thread.start()
    except KeyboardInterrupt:
        print("\n[*] Shutting down...")
    finally:
        sock.close()


# کلید RSA — در main() مقداردهی می‌شود
HOST_KEY = None

if __name__ == "__main__":
    main()
