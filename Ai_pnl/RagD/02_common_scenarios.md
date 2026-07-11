# Common Network Scenarios — Step by Step API Commands

**Purpose:** Full workflow examples for common real-world scenarios. Each scenario shows the exact sequence of API calls the AI agent should produce in COMMANDS format.

---

## SCENARIO 1: Set up a port for a new PC/workstation

**User says:** "configure port 5 for the new accounting PC on VLAN 10"

**Correct AI output:**
```
REPLY:
I'll configure port 5 (Fa0/5) for the accounting PC. I'll assign it to VLAN 10, set auto speed/duplex, and label it clearly.

COMMANDS:
GET /api/port/Fa0-5
PUT /api/port/Fa0-5/config {"description":"PC-Accounting","vlan_id":"10","mode":"access","speed":"auto","duplex":"auto"}
GET /api/port/Fa0-5
```

**Explanation:** First GET reads current state, PUT applies config, second GET verifies.

---

## SCENARIO 2: Set up a port for an IP camera

**User says:** "port 3 ro baraye doorbeen tandim kon" / "configure port 3 for a camera on VLAN 30"

**Correct AI output:**
```
REPLY:
I'll configure port 3 (Fa0/3) for an IP camera on VLAN 30. I'll enable port security with sticky MAC so only this camera can use the port.

COMMANDS:
GET /api/port/Fa0-3
PUT /api/port/Fa0-3/config {"description":"Camera-01","vlan_id":"30","mode":"access","speed":"100","duplex":"auto","port_security":true,"max_mac":1,"sticky_mac":true}
GET /api/port/Fa0-3
```

---

## SCENARIO 3: Set up a trunk/uplink port

**User says:** "configure port 16 as uplink to core switch"

**Correct AI output:**
```
REPLY:
I'll configure port 16 (Fa0/16) as a trunk uplink port to the core switch with native VLAN 1.

COMMANDS:
GET /api/port/Fa0-16
PUT /api/port/Fa0-16/config {"description":"Uplink-Core-SW","mode":"trunk","native_vlan":"1"}
GET /api/port/Fa0-16
```

---

## SCENARIO 4: Check all port statuses

**User says:** "show me all ports" / "what's the switch status?" / "which ports are active?"

**Correct AI output:**
```
REPLY:
Here's the current status of all switch ports:

COMMANDS:
GET /api/ports
```

---

## SCENARIO 5: Enable a disabled port

**User says:** "enable port 7" / "turn on port 7" / "پورت ۷ رو روشن کن"

**Correct AI output:**
```
REPLY:
I'll bring up port 7 (Fa0/7) now.

COMMANDS:
POST /api/port/Fa0-7/enable
GET /api/port/Fa0-7
```

---

## SCENARIO 6: Disable a port for security

**User says:** "disable port 12" / "shut down port 12" / "nobody should use port 12"

**Correct AI output:**
```
REPLY:
I'll shut down port 12 (Fa0/12). All traffic on this port will stop immediately.

COMMANDS:
POST /api/port/Fa0-12/disable
GET /api/port/Fa0-12
```

---

## SCENARIO 7: Fix a stuck device (port bounce)

**User says:** "the device on port 8 is not responding" / "bounce port 8" / "پورت ۸ رو ریلود کن"

**Correct AI output:**
```
REPLY:
I'll bounce port 8 (Fa0/8) — this will shut it down and bring it back up to force the device to reconnect. This takes about 3-4 seconds.

COMMANDS:
POST /api/port/Fa0-8/reload
GET /api/port/Fa0-8
```

---

## SCENARIO 8: Check what device is on a port

**User says:** "what device is connected to port 4?" / "show MAC address on port 4"

**Correct AI output:**
```
REPLY:
Let me check port 4 (Fa0/4) for connected devices and their MAC addresses.

COMMANDS:
GET /api/port/Fa0-4
```

---

## SCENARIO 9: Set up port security on existing port

**User says:** "enable port security on port 6, allow max 2 devices"

**Correct AI output:**
```
REPLY:
I'll enable port security on port 6 (Fa0/6) allowing a maximum of 2 MAC addresses.

COMMANDS:
PUT /api/port/Fa0-6/config {"port_security":true,"max_mac":2}
GET /api/port/Fa0-6
```

---

## SCENARIO 10: Change VLAN on a port

**User says:** "move port 9 from VLAN 10 to VLAN 20" / "change VLAN on port 9 to 20"

**Correct AI output:**
```
REPLY:
I'll reassign port 9 (Fa0/9) to VLAN 20.

COMMANDS:
GET /api/port/Fa0-9
PUT /api/port/Fa0-9/config {"vlan_id":"20","mode":"access"}
GET /api/port/Fa0-9
```

---

## SCENARIO 11: Set speed and duplex on a port

**User says:** "force port 2 to 100Mbps full duplex" / "set port 2 speed to 100"

**Correct AI output:**
```
REPLY:
I'll set port 2 (Fa0/2) to 100 Mbps full duplex.

COMMANDS:
PUT /api/port/Fa0-2/config {"speed":"100","duplex":"full"}
GET /api/port/Fa0-2
```

---

## SCENARIO 12: Reset a port to defaults

**User says:** "reset port 11 to factory defaults" / "clear all config on port 11"

**Correct AI output:**
```
REPLY:
I'll reset port 11 (Fa0/11) to factory defaults. All custom configuration (VLAN, speed, description, port security) will be cleared. The port will be left active on VLAN 1.

COMMANDS:
POST /api/port/Fa0-11/reset
GET /api/port/Fa0-11
```

---

## SCENARIO 13: Label/rename a port

**User says:** "set the description of port 5 to VoIP-Phone-Sales"

**Correct AI output:**
```
REPLY:
I'll update the description of port 5 (Fa0/5) to "VoIP-Phone-Sales".

COMMANDS:
PUT /api/port/Fa0-5/config {"description":"VoIP-Phone-Sales"}
GET /api/port/Fa0-5
```

---

## SCENARIO 14: Full VoIP phone setup

**User says:** "configure port 10 for a VoIP phone on voice VLAN 20"

**Correct AI output:**
```
REPLY:
I'll configure port 10 (Fa0/10) for VoIP — assigning it to voice VLAN 20 with 100Mbps full duplex for optimal voice quality.

COMMANDS:
GET /api/port/Fa0-10
PUT /api/port/Fa0-10/config {"description":"VoIP-Phone","vlan_id":"20","mode":"access","speed":"100","duplex":"full"}
GET /api/port/Fa0-10
```

---

## SCENARIO 15: Audit — find unauthorized devices

**User says:** "show me MAC addresses on all ports" / "check if any unknown devices are connected"

**Correct AI output:**
```
REPLY:
I'll check each active port for connected MAC addresses so you can identify any unknown devices.

COMMANDS:
GET /api/ports
GET /api/port/Fa0-1
GET /api/port/Fa0-2
GET /api/port/Fa0-3
GET /api/port/Fa0-4
GET /api/port/Fa0-5
GET /api/port/Fa0-6
GET /api/port/Fa0-7
GET /api/port/Fa0-8
```

Note: Only check ports that the switch_state shows as "up"

---

## SCENARIO 16: Disable port security on a port

**User says:** "remove port security from port 3" / "disable port security on port 3"

**Correct AI output:**
```
REPLY:
I'll disable port security on port 3 (Fa0/3). Any MAC address will be able to connect after this change.

COMMANDS:
PUT /api/port/Fa0-3/config {"port_security":false}
GET /api/port/Fa0-3
```

---

## RULES FOR SCENARIOS

1. Always GET a port before PUT to understand current state (when making changes)
2. Always GET a port after PUT/POST to verify the change was applied
3. For GET /api/ports (all ports): no verification GET needed
4. For disable/enable/reload: no pre-check GET needed (action is immediate)
5. Include GET /api/port/X after every change so the user sees the result
6. Port number format in URL: always Fa0-{number} (e.g., port 3 = Fa0-3)
