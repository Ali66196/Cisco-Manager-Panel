# Cisco IOS CLI Commands → Panel API Mapping

**Purpose:** This document maps every Cisco IOS interface command to its equivalent API call on the switch management panel. The AI agent must use this reference to translate user requests into correct API calls.

**Base URL:** http://localhost:5000
**Port name rule:** Replace every `/` with `-` in port names for URLs. Example: Fa0/3 → Fa0-3

---

## CATEGORY: Reading Switch State

### Get all ports status
```
Cisco CLI:  show interfaces status
Panel API:  GET /api/ports
Returns:    name, status (up/down/disabled), vlan, speed, duplex, mode, description, type
Use when:   User asks about overall switch status, which ports are active, port count
```

### Get single port details
```
Cisco CLI:  show interfaces Fa0/3
            show running-config interface Fa0/3
Panel API:  GET /api/port/Fa0-3
Returns:    All fields from GET /api/ports PLUS mac_addresses array, port_security, max_mac
Use when:   User asks about a specific port in detail, before making any changes to verify current state,
            after changes to verify they were applied
```

### Check switch connection
```
Panel API:  GET /api/status
Returns:    {"connected": true/false}
Use when:   Unsure if switch is connected before operations
```

---

## CATEGORY: Port Enable / Disable

### Enable a port (no shutdown)
```
Cisco CLI:  interface Fa0/3
             no shutdown
Panel API:  POST /api/port/Fa0-3/enable
Body:       none
Returns:    {"success": true}
User says:  "enable port 3", "turn on port 3", "bring up port 3", "no shutdown on port 3"
            "پورت ۳ رو فعال کن", "پورت ۳ رو روشن کن"
```

### Disable a port (shutdown)
```
Cisco CLI:  interface Fa0/3
             shutdown
Panel API:  POST /api/port/Fa0-3/disable
Body:       none
Returns:    {"success": true}
Warning:    Immediately drops all traffic on this port
User says:  "disable port 3", "shut down port 3", "shutdown port 3"
            "پورت ۳ رو خاموش کن", "پورت ۳ رو غیرفعال کن"
```

### Bounce / reload a port (shutdown then no shutdown)
```
Cisco CLI:  interface Fa0/3
             shutdown
            (2 second pause)
            interface Fa0/3
             no shutdown
Panel API:  POST /api/port/Fa0-3/reload
Body:       none
Returns:    {"success": true}
Note:       Takes 3-4 seconds to complete (blocking)
User says:  "bounce port 3", "restart port 3", "reset port 3 link",
            "device on port 3 is stuck", "force re-negotiation on port 3"
            "پورت ۳ رو ریلود کن", "دستگاه پورت ۳ قطع وصل می‌شه"
```

### Reset port to factory defaults
```
Cisco CLI:  interface Fa0/5
             no description
             no shutdown
             switchport mode access
             switchport access vlan 1
             no speed
             no duplex
             no switchport port-security
Panel API:  POST /api/port/Fa0-5/reset
Body:       none
Returns:    {"success": true}
Warning:    DESTRUCTIVE — all custom config is lost
User says:  "reset port 5 to default", "clear all config on port 5", "factory reset port 5"
            "پورت ۵ رو ریست کن", "همه تنظیمات پورت ۵ رو پاک کن"
```

---

## CATEGORY: VLAN Configuration

### Set access VLAN
```
Cisco CLI:  interface Fa0/3
             switchport mode access
             switchport access vlan 10
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"mode": "access", "vlan_id": "10"}
User says:  "put port 3 on VLAN 10", "assign VLAN 10 to port 3"
            "پورت ۳ رو روی VLAN 10 بذار"
```

### Set trunk mode
```
Cisco CLI:  interface Fa0/5
             switchport mode trunk
Panel API:  PUT /api/port/Fa0-5/config
Body:       {"mode": "trunk"}
User says:  "set port 5 as trunk", "make port 5 a trunk port"
            "پورت ۵ رو ترانک کن"
```

### Set trunk with native VLAN
```
Cisco CLI:  interface Fa0/5
             switchport mode trunk
             switchport trunk native vlan 99
Panel API:  PUT /api/port/Fa0-5/config
Body:       {"mode": "trunk", "native_vlan": "99"}
User says:  "set port 5 as trunk with native VLAN 99"
```

### Change only native VLAN (trunk port already configured)
```
Panel API:  PUT /api/port/Fa0-5/config
Body:       {"mode": "trunk", "native_vlan": "99"}
```

---

## CATEGORY: Speed Configuration

### Set speed to 100 Mbps
```
Cisco CLI:  interface Fa0/3
             speed 100
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"speed": "100"}
```

### Set speed to 10 Mbps
```
Cisco CLI:  interface Fa0/3
             speed 10
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"speed": "10"}
```

### Set speed to 1000 Mbps (1 Gbps)
```
Cisco CLI:  interface Fa0/3
             speed 1000
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"speed": "1000"}
```

### Set speed to auto
```
Cisco CLI:  interface Fa0/3
             no speed
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"speed": "auto"}
```

---

## CATEGORY: Duplex Configuration

### Set full duplex
```
Cisco CLI:  interface Fa0/3
             duplex full
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"duplex": "full"}
```

### Set half duplex
```
Cisco CLI:  interface Fa0/3
             duplex half
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"duplex": "half"}
```

### Set auto duplex
```
Cisco CLI:  interface Fa0/3
             duplex auto
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"duplex": "auto"}
```

---

## CATEGORY: Description

### Set description
```
Cisco CLI:  interface Fa0/3
             description Camera-01
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"description": "Camera-01"}
User says:  "label port 3 as Camera-01", "set port 3 description to Camera-01"
            "پورت ۳ رو Camera-01 بنام"
```

### Clear description
```
Cisco CLI:  interface Fa0/3
             no description
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"description": ""}
```

---

## CATEGORY: Port Security

### Enable port security (max 1 MAC)
```
Cisco CLI:  interface Fa0/3
             switchport port-security
             switchport port-security maximum 1
             switchport port-security violation restrict
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"port_security": true, "max_mac": 1}
User says:  "enable port security on port 3", "lock port 3 to one device"
            "port security پورت ۳ رو فعال کن"
```

### Enable port security with sticky MAC (lock to first device)
```
Cisco CLI:  interface Fa0/3
             switchport port-security
             switchport port-security maximum 1
             switchport port-security mac-address sticky
             switchport port-security violation restrict
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"port_security": true, "max_mac": 1, "sticky_mac": true}
User says:  "enable sticky MAC on port 3", "lock port 3 to the device connected"
            "sticky MAC پورت ۳ رو فعال کن"
```

### Allow multiple MAC addresses
```
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"port_security": true, "max_mac": 3}
User says:  "allow 3 devices on port 3", "set max 3 MACs on port 3"
```

### Disable port security
```
Cisco CLI:  interface Fa0/3
             no switchport port-security
Panel API:  PUT /api/port/Fa0-3/config
Body:       {"port_security": false}
```

---

## CATEGORY: Combined Configuration (Multiple settings at once)

### Full workstation setup
```
Panel API:  PUT /api/port/Fa0-1/config
Body: {
  "description": "PC-Accounting",
  "vlan_id": "10",
  "mode": "access",
  "speed": "auto",
  "duplex": "auto"
}
```

### Full IP camera setup
```
Panel API:  PUT /api/port/Fa0-3/config
Body: {
  "description": "Camera-01",
  "vlan_id": "30",
  "mode": "access",
  "speed": "100",
  "duplex": "auto",
  "port_security": true,
  "max_mac": 1,
  "sticky_mac": true
}
```

### Full VoIP phone setup
```
Panel API:  PUT /api/port/Fa0-5/config
Body: {
  "description": "VoIP-Phone-01",
  "vlan_id": "20",
  "mode": "access",
  "speed": "100",
  "duplex": "full"
}
```

### Uplink / trunk port setup
```
Panel API:  PUT /api/port/Fa0-16/config
Body: {
  "description": "Uplink-Core-SW",
  "mode": "trunk",
  "native_vlan": "1"
}
```

### Printer / IoT device setup
```
Panel API:  PUT /api/port/Fa0-8/config
Body: {
  "description": "Printer-Floor2",
  "vlan_id": "40",
  "mode": "access",
  "speed": "100",
  "port_security": true,
  "max_mac": 1
}
```

---

## IMPORTANT API RULES

1. Port names in URL: always use hyphen. Fa0/3 → Fa0-3, Gi0/1 → Gi0-1
2. PUT /config only changes fields you send — other fields stay unchanged
3. When sending vlan_id, always also send mode (and vice versa)
4. max_mac and sticky_mac only work when port_security is also in the request
5. native_vlan only applied when mode is "trunk"
6. All config changes are saved to switch memory automatically (write memory)
