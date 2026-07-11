# Cisco AI Switch Manager

An AI-powered Cisco switch management platform that combines a web-based administration panel with a Retrieval-Augmented Generation (RAG) assistant capable of translating natural language requests into validated network operations.

This project was developed as a final associate degree project in Computer Networks and integrates Cisco networking, web development, and artificial intelligence into a single management platform.

---

## Overview

Cisco AI Switch Manager consists of two independent components:

- **Cisco Switch Panel** – A Flask-based web interface for direct switch management through SSH.
- **AI Assistant** – A RAG-powered chatbot that allows administrators to configure switches using natural language.

The AI layer is completely optional. Every operation performed by the chatbot is executed through the same REST API used by the management panel.

---

## Architecture

```text
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Chat Panel      │ ───▶ │       n8n         │ ───▶ │      Qdrant       │
│  (HTML/CSS/JS)    │      │  Agent 1: Planner │      │   Vector Database │
│                   │ ◀─── │  Agent 2: Executor│      │       (RAG)        │
└─────────┬─────────┘      └──────────────────┘      └──────────────────┘
          │
          │ REST API
          ▼
┌──────────────────┐      ┌──────────────────┐      ┌──────────────────┐
│   Cisco Panel     │ ───▶ │  switch_manager   │ ───▶ │   Cisco Switch    │
│    Flask + API    │      │  Netmiko / SSH    │      │ Real or Emulated  │
└──────────────────┘      └──────────────────┘      └──────────────────┘
```

---

## Project Structure

```text
ciscoprj/
├── cisco_panel/
│   ├── app.py
│   ├── switch_manager.py
│   ├── api_routes.py
│   ├── API_DOCUMENTATION.md
│   ├── requirements.txt
│   ├── static/
│   └── templates/
│
├── cisco_emulator/
│   └── fake_switch.py
│
└── Ai_pnl/
    ├── chat/
    └── RagD/
        ├── 01_cisco_cli_to_api_mapping.md
        ├── 02_common_scenarios.md
        ├── 03_output_format_rules.md
        └── 04_troubleshooting.md
```

---

# Features

## Web Management Panel

- SSH connection to Cisco switches using Netmiko
- Visual interface for monitoring all switch ports
- Configure:
  - VLAN
  - Access / Trunk mode
  - Speed
  - Duplex
  - Description
  - Port Security
- Enable, disable, reset, and reload interfaces
- Independent REST API for external integrations

---

## AI Assistant

- Configure switches using natural language
- RAG knowledge base powered by Qdrant
- Two-Agent architecture
  - Planner Agent
  - Executor Agent
- Automatic GET → MODIFY → GET verification workflow
- Executes only validated API operations
- The switch management panel is never directly exposed to the Internet

---

# Installation

## Requirements

```bash
pip install -r cisco_panel/requirements.txt
```

---

## Running with the Emulator

Start the emulated Cisco switch:

```bash
python cisco_emulator/fake_switch.py
```

Start the Flask application:

```bash
python cisco_panel/app.py
```

Open your browser:

```
http://localhost:5000
```

Default emulator credentials:

| Item | Value |
|------|-------|
| Host | 127.0.0.1 |
| Port | 2222 |
| Username | cisco |
| Password | cisco123 |

---

## Running with a Real Cisco Switch

No code changes are required.

Simply enter the switch IP address and SSH credentials in the connection page.

---

# AI Setup (Optional)

1. Index the documents inside `Ai_pnl/RagD` into a Qdrant instance.
2. Create the two-Agent workflow in n8n.
3. Update the webhook URL inside:

```
Ai_pnl/chat/script.js
```

4. Open:

```
Ai_pnl/chat/index.html
```

---

# Technologies

| Layer | Technology |
|--------|------------|
| Backend | Python |
| Web Framework | Flask |
| Switch Communication | Netmiko, SSH |
| REST API | Flask |
| Frontend | HTML, CSS, JavaScript |
| AI Workflow | n8n |
| Retrieval | RAG |
| Vector Database | Qdrant |
| Switch Emulator | Paramiko |

---

# Project Goals

- Simplify Cisco switch management
- Provide a visual interface for administrators
- Demonstrate how AI can safely automate network configuration
- Showcase the integration of Networking, REST APIs, and Retrieval-Augmented Generation (RAG)

---

## License

This project was developed for educational purposes as a final-year networking project.
