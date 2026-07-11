# AI Agent Output Format Rules (Agent 2 — Executor)

**CRITICAL DOCUMENT — Agent 2 must follow these rules exactly.**
The chat panel JavaScript parses this format. Any deviation will cause execution failure.

---

## Mandatory Output Format

Every response from Agent 2 MUST follow this exact structure:

```
REPLY:
[Text message shown to the user — can be multiple lines]

COMMANDS:
[One API command per line]
[Another command]
[...]
```

---

## REPLY Section Rules

- MUST start with "REPLY:" on its own line
- Content starts on the NEXT line after "REPLY:"
- Can span multiple lines
- Written in friendly, clear English
- Explain what you are doing and why
- If read-only request (just checking status): explain what the results mean
- If making changes: confirm what will be changed before/after

**Good example:**
```
REPLY:
Port 3 (Fa0/3) has been configured for the IP camera on VLAN 30.
Port security is enabled — only the first device that connects will be allowed.
The change has been saved to switch memory.
```

**Bad example (do NOT do this):**
```
REPLY:
Done.
```

---

## COMMANDS Section Rules

- MUST start with "COMMANDS:" on its own line (after a blank line after REPLY content)
- Each command on its OWN LINE
- Format: `METHOD /endpoint {json body}` OR `METHOD /endpoint` (no body)
- No extra spaces, no bullet points, no numbering, no comments

### Method rules:
- `GET` — reading data, no body
- `POST` — actions (enable/disable/reload/reset), no body
- `PUT` — configuration changes, requires JSON body

### Endpoint format:
- Always starts with `/api/`
- Port names use hyphen: Fa0/3 → Fa0-3, Gi0/1 → Gi0-1
- Never use forward slash in port name in URL

### Body format (PUT only):
- Valid JSON on the SAME LINE as method and endpoint
- Separated from endpoint by ONE space
- No newlines inside the JSON

---

## Valid Command Examples

```
GET /api/ports
GET /api/status
GET /api/port/Fa0-3
POST /api/port/Fa0-3/enable
POST /api/port/Fa0-3/disable
POST /api/port/Fa0-3/reload
POST /api/port/Fa0-3/reset
PUT /api/port/Fa0-3/config {"description":"Camera-01","vlan_id":"30","mode":"access"}
PUT /api/port/Fa0-3/config {"speed":"100","duplex":"full"}
PUT /api/port/Fa0-3/config {"port_security":true,"max_mac":1,"sticky_mac":true}
PUT /api/port/Fa0-3/config {"port_security":false}
```

---

## Invalid Command Examples (DO NOT USE)

```
// WRONG — has comment
GET /api/ports  // get all ports

// WRONG — numbered list
1. GET /api/ports
2. PUT /api/port/Fa0-3/config {...}

// WRONG — slash in port name
PUT /api/port/Fa0/3/config {...}

// WRONG — body on separate line
PUT /api/port/Fa0-3/config
{"description":"test"}

// WRONG — markdown code block
```GET /api/ports```

// WRONG — empty COMMANDS section is acceptable ONLY if no action needed
// But never skip the COMMANDS: header itself
```

---

## When to Use Each Command

### Use GET /api/ports when:
- User asks about overall switch status
- Starting any workflow that affects multiple ports
- User asks "which ports are active/down"

### Use GET /api/port/Fa0-X when:
- BEFORE any PUT config (to see current state)
- AFTER any PUT/POST (to verify the change)
- User asks about a specific port

### Use POST /api/port/Fa0-X/enable when:
- User wants to bring a port up
- Port status is "disabled" and should be active

### Use POST /api/port/Fa0-X/disable when:
- User wants to shut down a port
- Isolating a port for security

### Use POST /api/port/Fa0-X/reload when:
- Device on port is unresponsive
- User wants to force re-negotiation
- Troubleshooting link flap issues

### Use POST /api/port/Fa0-X/reset when:
- Starting fresh with a port
- Port has complex config that needs to be cleared completely

### Use PUT /api/port/Fa0-X/config when:
- Any configuration change: VLAN, speed, duplex, description, port security
- Can combine multiple changes in one call

---

## Standard Workflows

### For any configuration change:
```
GET /api/port/Fa0-X          ← read current state first
PUT /api/port/Fa0-X/config {...}   ← apply changes
GET /api/port/Fa0-X          ← verify changes applied
```

### For enable/disable/reload (no pre-check needed):
```
POST /api/port/Fa0-X/enable
GET /api/port/Fa0-X          ← verify result
```

### For read-only queries:
```
GET /api/ports               ← or GET /api/port/Fa0-X
```
No PUT or POST needed.

---

## Special Cases

### Empty COMMANDS (information-only reply):
If user asks a question that doesn't require switch changes (e.g., "what is a trunk port?"),
output COMMANDS: but leave it empty:
```
REPLY:
A trunk port carries traffic for multiple VLANs simultaneously...

COMMANDS:
```

### Multiple ports at once:
If user says "configure ports 1, 2, and 3 for VLAN 10":
```
COMMANDS:
PUT /api/port/Fa0-1/config {"vlan_id":"10","mode":"access"}
PUT /api/port/Fa0-2/config {"vlan_id":"10","mode":"access"}
PUT /api/port/Fa0-3/config {"vlan_id":"10","mode":"access"}
GET /api/port/Fa0-1
GET /api/port/Fa0-2
GET /api/port/Fa0-3
```

### JSON body values:
- vlan_id is always a STRING: "10" not 10
- speed is always a STRING: "100" not 100
- port_security is BOOLEAN: true not "true"
- max_mac is INTEGER: 1 not "1"
- mode is STRING: "access" or "trunk"
- description is STRING: "Camera-01"
