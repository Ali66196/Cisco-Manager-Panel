# Cisco Switch Management Panel — API Documentation

> **Audience:** AI agents and automated services  
> **Base URL:** `http://localhost:5000`  
> **All responses:** `Content-Type: application/json`  
> **Authentication:** None required — API is designed for local/trusted service use only

---

## Table of Contents

1. [Overview](#overview)
2. [Port Naming Convention](#port-naming-convention)
3. [Connection Management](#connection-management)
   - [POST /api/connect](#post-apiconnect)
   - [POST /api/disconnect](#post-apidisconnect)
   - [GET /api/status](#get-apistatus)
4. [Port Information](#port-information)
   - [GET /api/ports](#get-apiports)
   - [GET /api/port/:port_name](#get-apiportport_name)
5. [Port Actions](#port-actions)
   - [POST /api/port/:port_name/enable](#post-apiportport_nameenable)
   - [POST /api/port/:port_name/disable](#post-apiportport_namedisable)
   - [POST /api/port/:port_name/reload](#post-apiportport_namereload)
   - [POST /api/port/:port_name/reset](#post-apiportport_namereset)
6. [Port Configuration](#port-configuration)
   - [PUT /api/port/:port_name/config](#put-apiportport_nameconfig)
7. [Error Reference](#error-reference)
8. [Field Reference](#field-reference)
9. [Workflow Examples for AI Agent](#workflow-examples-for-ai-agent)

---

## Overview

This API provides full programmatic control over a Cisco IOS switch via SSH. It is designed to be consumed by an AI agent that can read switch state, reason about it, and apply configuration changes — all through simple HTTP calls.

**Typical agent workflow:**

```
1. Connect to switch        → POST /api/connect
2. Check connection         → GET  /api/status
3. Read all port states     → GET  /api/ports
4. Inspect a specific port  → GET  /api/port/Fa0-1
5. Apply changes            → PUT  /api/port/Fa0-1/config
6. Verify the change        → GET  /api/port/Fa0-1
7. Disconnect when done     → POST /api/disconnect
```

**Important behavioral notes:**

- Every endpoint except `/api/connect`, `/api/disconnect`, and `/api/status` requires an active SSH connection. If not connected, all such endpoints return HTTP `400`.
- Configuration changes (`PUT /config`, `enable`, `disable`, `reload`, `reset`) are **immediately written to the switch** and followed by a `write memory` call, so changes persist across reboots.
- The API is **stateless from the agent's perspective** — the SSH session is maintained server-side. The agent does not need to manage connection state between calls.

---

## Port Naming Convention

Cisco port names use a forward slash (`/`) which is not valid in a URL path segment. This API uses a **hyphen (`-`) as a substitute**.

| Real port name | URL form   |
|----------------|------------|
| `Fa0/1`        | `Fa0-1`    |
| `Fa0/12`       | `Fa0-12`   |
| `Gi0/1`        | `Gi0-1`    |
| `Gi1/0/24`     | `Gi1-0-24` |

The conversion rule: **replace every `/` with `-`** in the port name when constructing the URL.

---

## Connection Management

### POST /api/connect

Establishes an SSH connection to a Cisco IOS switch. Must be called before any port operations.

**Request body:**

```json
{
  "ip":       "127.0.0.1",
  "port":     2222,
  "username": "cisco",
  "password": "cisco123"
}
```

| Field      | Type    | Required | Default | Description                        |
|------------|---------|----------|---------|------------------------------------|
| `ip`       | string  | yes      | —       | Switch IP address or hostname      |
| `port`     | integer | no       | `22`    | SSH port                           |
| `username` | string  | yes      | —       | Switch SSH username                |
| `password` | string  | yes      | —       | Switch SSH password                |

**Response — success:**

```json
{
  "success": true,
  "message": "Connection successful"
}
```

**Response — authentication failure:**

```json
{
  "success": false,
  "message": "Authentication failed: wrong username or password"
}
```

**Response — switch unreachable:**

```json
{
  "success": false,
  "message": "Connection timed out: switch unreachable"
}
```

**Response — other error:**

```json
{
  "success": false,
  "message": "No existing session"
}
```

**HTTP status:** always `200` — check `success` field to determine outcome.

---

### POST /api/disconnect

Closes the active SSH session and releases the connection.

**Request body:** none required

**Response:**

```json
{
  "success": true,
  "message": "Disconnected"
}
```

**HTTP status:** `200`

> Calling this endpoint when no connection is active is safe — it will not error.

---

### GET /api/status

Returns whether an active SSH connection currently exists.

**Request body:** none

**Response:**

```json
{
  "connected": true
}
```

| Field       | Type    | Description                              |
|-------------|---------|------------------------------------------|
| `connected` | boolean | `true` if SSH session is active          |

**HTTP status:** `200`

> The agent should call this before port operations if unsure about connection state, or after a network interruption.

---

## Port Information

### GET /api/ports

Returns the status of all ports (up to 16) as read from `show interfaces status`. This is the lightweight bulk endpoint — use it for dashboarding or scanning overall switch state.

**Request body:** none

**Response — success:**

```json
{
  "success": true,
  "ports": [
    {
      "name":        "Fa0/1",
      "index":       1,
      "status":      "up",
      "vlan":        "10",
      "speed":       "100",
      "duplex":      "a-full",
      "mode":        "access",
      "description": "PC-Accounting",
      "type":        "FastEthernet"
    },
    {
      "name":        "Fa0/5",
      "index":       5,
      "status":      "up",
      "vlan":        "1",
      "speed":       "100",
      "duplex":      "a-full",
      "mode":        "trunk",
      "description": "Uplink-to-Core",
      "type":        "FastEthernet"
    },
    {
      "name":        "Fa0/16",
      "index":       16,
      "status":      "down",
      "vlan":        "1",
      "speed":       "auto",
      "duplex":      "auto",
      "mode":        "access",
      "description": "",
      "type":        "FastEthernet"
    }
  ]
}
```

**Port object fields:**

| Field         | Type    | Description                                                      |
|---------------|---------|------------------------------------------------------------------|
| `name`        | string  | Port identifier as reported by the switch (`Fa0/1`, `Gi0/1`)    |
| `index`       | integer | Sequential position (1–16) for UI mapping                        |
| `status`      | string  | `"up"` / `"down"` / `"disabled"` — see [Field Reference](#field-reference) |
| `vlan`        | string  | Active VLAN ID. For trunk ports this reflects the native VLAN   |
| `speed`       | string  | `"auto"`, `"10"`, `"100"`, `"1000"`                             |
| `duplex`      | string  | Raw Cisco value: `"a-full"`, `"a-half"`, `"full"`, `"half"`, `"auto"` |
| `mode`        | string  | `"access"` or `"trunk"`                                          |
| `description` | string  | Port label configured on the switch. Empty string if none        |
| `type`        | string  | `"FastEthernet"`, `"GigabitEthernet"`, `"TenGigabitEthernet"`, `"Ethernet"` |

**Response — not connected (HTTP 400):**

```json
{
  "success": false,
  "error": "Not connected to switch"
}
```

---

### GET /api/port/:port_name

Returns detailed information about a single port, including running configuration and connected MAC addresses. Executes two commands on the switch: `show interfaces <port>` and `show running-config interface <port>`.

**URL parameter:** port name in hyphen form, e.g. `Fa0-1`

**Example request:**

```
GET /api/port/Fa0-3
```

**Response — success:**

```json
{
  "success": true,
  "port": {
    "name":          "Fa0/3",
    "status":        "up",
    "description":   "IP-Camera-01",
    "vlan":          "20",
    "mode":          "access",
    "speed":         "10",
    "duplex":        "half",
    "port_security": true,
    "max_mac":       1,
    "type":          "FastEthernet",
    "mac_addresses": [
      "aabb.cc00.0100"
    ]
  }
}
```

**Port detail fields:**

| Field           | Type          | Description                                                                 |
|-----------------|---------------|-----------------------------------------------------------------------------|
| `name`          | string        | Full port name with slash (`Fa0/3`)                                         |
| `status`        | string        | `"up"` / `"down"` / `"disabled"`                                            |
| `description`   | string        | Configured description. Empty string if not set                             |
| `vlan`          | string        | Access VLAN ID (access mode) or native VLAN (trunk mode)                   |
| `mode`          | string        | `"access"` or `"trunk"`                                                     |
| `speed`         | string        | `"auto"` if not explicitly set, otherwise `"10"`, `"100"`, `"1000"`        |
| `duplex`        | string        | `"auto"` if not explicitly set, otherwise `"full"` or `"half"`             |
| `port_security` | boolean       | Whether port-security is enabled                                            |
| `max_mac`       | integer       | Maximum allowed MAC addresses (only meaningful when `port_security: true`) |
| `type`          | string        | Port hardware type                                                          |
| `mac_addresses` | array[string] | List of MAC addresses learned on this port. Empty array if none             |

**Response — not connected (HTTP 400):**

```json
{
  "success": false,
  "error": "Not connected to switch"
}
```

---

## Port Actions

All action endpoints use `POST` with no required request body. They return a simple success/failure response.

---

### POST /api/port/:port_name/enable

Brings the port up by issuing `no shutdown`. Writes config to memory.

**Example request:**

```
POST /api/port/Fa0-7/enable
```

**Response — success:**

```json
{
  "success": true
}
```

**Response — failure:**

```json
{
  "success": false
}
```

**Cisco commands executed:**
```
interface Fa0/7
 no shutdown
write memory
```

---

### POST /api/port/:port_name/disable

Shuts the port down by issuing `shutdown`. Writes config to memory.

**Example request:**

```
POST /api/port/Fa0-7/disable
```

**Response:**

```json
{
  "success": true
}
```

**Cisco commands executed:**
```
interface Fa0/7
 shutdown
write memory
```

> **Warning:** This immediately drops all traffic on the port. Verify the correct port before calling.

---

### POST /api/port/:port_name/reload

Performs a port bounce: `shutdown` → 2-second pause → `no shutdown`. Useful for resetting a stuck port or forcing a connected device to re-negotiate.

**Example request:**

```
POST /api/port/Fa0-3/reload
```

**Response:**

```json
{
  "success": true
}
```

**Cisco commands executed:**
```
interface Fa0/3
 shutdown
(2 second pause)
interface Fa0/3
 no shutdown
write memory
```

> Note: The 2-second pause blocks the HTTP response. Expect this call to take ~3–4 seconds to complete.

---

### POST /api/port/:port_name/reset

Resets the port to factory defaults. Clears description, VLAN, speed, duplex, and port-security configuration. Port is left in `no shutdown` state on VLAN 1.

**Example request:**

```
POST /api/port/Fa0-5/reset
```

**Response:**

```json
{
  "success": true
}
```

**Cisco commands executed:**
```
interface Fa0/5
 no description
 no shutdown
 switchport mode access
 switchport access vlan 1
 no speed
 no duplex
 no switchport port-security
write memory
```

> **Warning:** This is destructive. All custom configuration on the port is lost.

---

## Port Configuration

### PUT /api/port/:port_name/config

Applies one or more configuration changes to a port in a single request. Only fields present in the request body are applied — omitted fields are left unchanged. Each field is applied independently; partial success is possible.

**Example request:**

```
PUT /api/port/Fa0-2/config
```

**Request body:**

```json
{
  "description":   "VOIP-Phone-02",
  "vlan_id":       "20",
  "mode":          "access",
  "native_vlan":   null,
  "speed":         "100",
  "duplex":        "full",
  "port_security": true,
  "max_mac":       2,
  "sticky_mac":    false
}
```

**All request body fields:**

| Field           | Type    | Required | Accepted values                            | Description                                                           |
|-----------------|---------|----------|--------------------------------------------|-----------------------------------------------------------------------|
| `description`   | string  | no       | any string                                 | Sets port description. Send `""` to clear it                          |
| `vlan_id`       | string  | no       | `"1"` – `"4094"`                           | VLAN to assign. Required when `mode` is `"access"`                   |
| `mode`          | string  | no       | `"access"` / `"trunk"`                     | Switchport mode                                                       |
| `native_vlan`   | string  | no       | `"1"` – `"4094"` or `null`                 | Native VLAN for trunk ports. Ignored when `mode` is `"access"`       |
| `speed`         | string  | no       | `"auto"` / `"10"` / `"100"` / `"1000"`    | Interface speed                                                       |
| `duplex`        | string  | no       | `"auto"` / `"full"` / `"half"`             | Interface duplex mode                                                 |
| `port_security` | boolean | no       | `true` / `false`                           | Enable or disable port-security                                       |
| `max_mac`       | integer | no       | `1` – `132`                                | Max MAC addresses allowed. Only applied when `port_security` is sent |
| `sticky_mac`    | boolean | no       | `true` / `false`                           | Enable sticky MAC learning. Only applied when `port_security` is sent |

**Field application rules:**

- `vlan_id` and `mode` are applied together. If only one is sent, the other defaults to `"1"` / `"access"`. Best practice: always send both together.
- `max_mac` and `sticky_mac` are only processed when `port_security` is present in the request.
- `native_vlan` is only applied when `mode` is `"trunk"`.

**Response — all changes applied:**

```json
{
  "success": true,
  "results": {
    "description":   true,
    "vlan":          true,
    "speed":         true,
    "duplex":        true,
    "port_security": true
  }
}
```

**Response — partial failure (some changes applied, some failed):**

```json
{
  "success": false,
  "results": {
    "description": true,
    "vlan":        false,
    "speed":       true
  }
}
```

**Response — no fields sent:**

```json
{
  "success": false,
  "results": {}
}
```

The `results` object contains one key per field group that was sent:

| Key in `results`  | Triggered by fields                              |
|-------------------|--------------------------------------------------|
| `description`     | `description`                                    |
| `vlan`            | `vlan_id` and/or `mode` (and `native_vlan`)      |
| `speed`           | `speed`                                          |
| `duplex`          | `duplex`                                         |
| `port_security`   | `port_security` (and `max_mac`, `sticky_mac`)    |

**Response — not connected (HTTP 400):**

```json
{
  "success": false,
  "error": "Not connected to switch"
}
```

---

## Error Reference

### HTTP 400 — Not Connected

Returned by all port operation endpoints when no active SSH session exists.

```json
{
  "success": false,
  "error": "Not connected to switch"
}
```

**Resolution:** Call `POST /api/connect` first, verify with `GET /api/status`.

### success: false with HTTP 200

Some endpoints return HTTP 200 but `"success": false`. This means the request was valid but the switch operation failed (e.g. SSH command error, Netmiko exception).

**Resolution:** Check switch connectivity, verify port name is correct, retry.

### Empty results object

`PUT /api/port/.../config` with no recognized fields returns `success: false` and an empty `results` object. This means the request body had no actionable fields.

---

## Field Reference

### status values

| Value        | Meaning                                                      |
|--------------|--------------------------------------------------------------|
| `"up"`       | Port is active and a link is detected                        |
| `"down"`     | Port is active (no shutdown) but no link detected            |
| `"disabled"` | Port has been administratively shut down (`shutdown` command)|

### duplex values (from switch)

| Value     | Meaning                          |
|-----------|----------------------------------|
| `"a-full"`| Auto-negotiated, resolved full   |
| `"a-half"`| Auto-negotiated, resolved half   |
| `"full"`  | Manually set full duplex         |
| `"half"`  | Manually set half duplex         |
| `"auto"`  | Auto-negotiation, not yet resolved |

### speed values (from switch)

| Value    | Meaning                 |
|----------|-------------------------|
| `"auto"` | Not explicitly set      |
| `"10"`   | 10 Mbps                 |
| `"100"`  | 100 Mbps                |
| `"1000"` | 1000 Mbps (1 Gbps)      |

### port type values

| Value                | Detected from port name prefix |
|----------------------|-------------------------------|
| `"FastEthernet"`     | `Fa`                          |
| `"GigabitEthernet"`  | `Gi`                          |
| `"TenGigabitEthernet"` | `Te`                        |
| `"Ethernet"`         | anything else                 |

---

## Workflow Examples for AI Agent

### Workflow 1 — Connect and audit all ports

```http
POST /api/connect
{
  "ip": "192.168.1.1",
  "port": 22,
  "username": "admin",
  "password": "cisco123"
}

→ { "success": true, "message": "Connection successful" }

GET /api/ports

→ { "success": true, "ports": [ ... ] }
```

Use the `ports` array to identify any port with `"status": "down"` or unusual VLAN assignments.

---

### Workflow 2 — Reconfigure a port for a new device

```http
GET /api/port/Fa0-4
→ Read current state before making changes

PUT /api/port/Fa0-4/config
{
  "description": "New-Workstation",
  "vlan_id": "30",
  "mode": "access",
  "speed": "auto",
  "duplex": "auto"
}
→ { "success": true, "results": { "description": true, "vlan": true, "speed": true, "duplex": true } }

GET /api/port/Fa0-4
→ Verify changes were applied correctly
```

---

### Workflow 3 — Enable port-security on a camera port

```http
PUT /api/port/Fa0-3/config
{
  "port_security": true,
  "max_mac": 1,
  "sticky_mac": true
}
→ { "success": true, "results": { "port_security": true } }
```

With `sticky_mac: true`, the switch will learn the first MAC address and lock the port to it automatically.

---

### Workflow 4 — Bounce a port to recover a stuck device

```http
POST /api/port/Fa0-8/reload
→ (waits ~3-4 seconds)
→ { "success": true }

GET /api/port/Fa0-8
→ Check if status is now "up"
```

---

### Workflow 5 — Configure an uplink trunk port

```http
PUT /api/port/Fa0-5/config
{
  "description": "Uplink-to-Core-SW",
  "mode": "trunk",
  "native_vlan": "1"
}
→ { "success": true, "results": { "description": true, "vlan": true } }
```

---

### Workflow 6 — Disable and re-enable a port

```http
POST /api/port/Fa0-12/disable
→ { "success": true }

GET /api/port/Fa0-12
→ { "port": { "status": "disabled", ... } }

POST /api/port/Fa0-12/enable
→ { "success": true }
```

---

### Workflow 7 — Check if any port has unknown devices (MAC audit)

```http
GET /api/ports
→ For each port with "status": "up"

GET /api/port/Fa0-1
→ { "port": { "mac_addresses": ["0050.7966.6800"], ... } }

GET /api/port/Fa0-2
→ { "port": { "mac_addresses": ["0050.7966.6801", "0050.7966.6802"], ... } }
```

Compare `mac_addresses` against known device inventory to detect unauthorized connections.

---

*Last updated: June 2026 | Cisco Switch Management Panel v1.0*
