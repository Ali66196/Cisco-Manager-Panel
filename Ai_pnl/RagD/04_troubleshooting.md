# Troubleshooting Guide — Problems and API Solutions

**Purpose:** Common network problems described in natural language, with the API commands to diagnose and fix them.

---

## PROBLEM: Device not getting network / no connectivity

**User says:** "the PC on port 5 can't connect", "no internet on port 5", "port 5 not working"

**Diagnosis steps and API commands:**
```
REPLY:
Let me diagnose port 5. I'll check its status, VLAN assignment, and whether a cable is detected.

COMMANDS:
GET /api/port/Fa0-5
```

**What to look for in result:**
- status: "disabled" → port was shut down, use enable
- status: "down" → no cable detected or device off
- status: "up" → port is fine, problem is elsewhere (IP config, DHCP, VLAN routing)
- wrong vlan → reassign to correct VLAN

**If port is disabled:**
```
POST /api/port/Fa0-5/enable
GET /api/port/Fa0-5
```

**If port is up but device has no IP (wrong VLAN):**
```
PUT /api/port/Fa0-5/config {"vlan_id":"10","mode":"access"}
GET /api/port/Fa0-5
```

---

## PROBLEM: Device keeps losing connection / intermittent link

**User says:** "port 8 keeps dropping", "device on port 8 disconnects randomly", "link flapping on port 8"

**Solution:**
```
REPLY:
I'll bounce port 8 to force a clean re-negotiation. I'll also check the speed/duplex settings — mismatched duplex is a common cause of intermittent connectivity.

COMMANDS:
GET /api/port/Fa0-8
POST /api/port/Fa0-8/reload
GET /api/port/Fa0-8
```

**If duplex shows "half" but should be full:**
```
PUT /api/port/Fa0-8/config {"speed":"100","duplex":"full"}
GET /api/port/Fa0-8
```

---

## PROBLEM: Unauthorized device connected

**User says:** "unknown device on port 6", "someone plugged into port 6 without permission"

**Solution:**
```
REPLY:
I'll check what's connected to port 6 and then disable the port to prevent unauthorized access.

COMMANDS:
GET /api/port/Fa0-6
POST /api/port/Fa0-6/disable
```

**If you want to lock it to authorized device only:**
```
PUT /api/port/Fa0-6/config {"port_security":true,"max_mac":1,"sticky_mac":true}
POST /api/port/Fa0-6/enable
GET /api/port/Fa0-6
```

---

## PROBLEM: Port security violation (too many MACs)

**User says:** "port security violation on port 3", "port 3 is in err-disabled"

**Note:** err-disabled is not directly resolvable via this API. The reload action will help.

**Solution:**
```
REPLY:
I'll reset port 3 to clear any port security violations and then reconfigure it properly.

COMMANDS:
POST /api/port/Fa0-3/reset
PUT /api/port/Fa0-3/config {"port_security":true,"max_mac":1,"sticky_mac":true}
GET /api/port/Fa0-3
```

---

## PROBLEM: Wrong VLAN — device in wrong network segment

**User says:** "port 4 is in the wrong VLAN", "move port 4 from VLAN 10 to VLAN 20"

**Solution:**
```
REPLY:
I'll move port 4 (Fa0/4) from its current VLAN to VLAN 20.

COMMANDS:
GET /api/port/Fa0-4
PUT /api/port/Fa0-4/config {"vlan_id":"20","mode":"access"}
GET /api/port/Fa0-4
```

---

## PROBLEM: Trunk port not passing all VLANs

**User says:** "port 16 trunk not working", "VLANs not passing on uplink"

**Solution:**
```
REPLY:
I'll verify and reconfigure port 16 as a proper trunk port.

COMMANDS:
GET /api/port/Fa0-16
PUT /api/port/Fa0-16/config {"mode":"trunk","native_vlan":"1"}
GET /api/port/Fa0-16
```

---

## PROBLEM: Switch port showing "down" but device is connected

**User says:** "I plugged in the cable but port 2 still shows down"

**Diagnosis:**
```
REPLY:
Let me check port 2's configuration. It might be administratively disabled, or there could be a speed/duplex mismatch.

COMMANDS:
GET /api/port/Fa0-2
```

**If disabled → enable it:**
```
POST /api/port/Fa0-2/enable
GET /api/port/Fa0-2
```

**If up but still having issues → bounce it:**
```
POST /api/port/Fa0-2/reload
GET /api/port/Fa0-2
```

---

## PROBLEM: Need to check all down ports

**User says:** "show me all the ports that are down", "which ports have problems?"

**Solution:**
```
REPLY:
I'll pull the full switch status so you can see which ports are down or disabled.

COMMANDS:
GET /api/ports
```

Then in REPLY, explain: ports with status "down" have no cable/device, ports with "disabled" were manually shut down.

---

## PROBLEM: Port was accidentally reset, need to reconfigure

**User says:** "port 7 was reset and now nothing works"

**Solution depends on what device is on the port. For a typical PC:**
```
REPLY:
I'll reconfigure port 7 (Fa0/7) for a standard workstation on VLAN 10.

COMMANDS:
PUT /api/port/Fa0-7/config {"description":"PC-Floor2","vlan_id":"10","mode":"access","speed":"auto","duplex":"auto"}
GET /api/port/Fa0-7
```

---

## PROBLEM: Speed mismatch causing poor performance

**User says:** "network is slow on port 9", "getting only 10Mbps on port 9"

**Solution:**
```
REPLY:
I'll check port 9's current speed and duplex settings and force them to the optimal values.

COMMANDS:
GET /api/port/Fa0-9
PUT /api/port/Fa0-9/config {"speed":"100","duplex":"full"}
GET /api/port/Fa0-9
```

---

## PROBLEM: Need to isolate a port for maintenance

**User says:** "I need to take port 12 offline for maintenance"

**Solution:**
```
REPLY:
I'll shut down port 12 (Fa0/12) for maintenance. Remember to re-enable it when done.

COMMANDS:
POST /api/port/Fa0-12/disable
GET /api/port/Fa0-12
```
