# CloudPulse Agent Installation & Setup Guide

This document describes how to install, register, and run the **CloudPulse Monitoring Agent** on Windows and Linux machines.

---

## 1. Prerequisites

- Python 3.9+ installed.
- Network connectivity to the CloudPulse Backend (HTTP/HTTPS).

---

## 2. Installation on Windows

### Step 1: Open PowerShell or Command Prompt
Navigate to your preferred directory:
```powershell
git clone <repository_url> cloudpulse
cd cloudpulse\agent
```

### Step 2: Install Dependencies
```powershell
pip install -r requirements.txt
```

### Step 3: Test Telemetry Collection
Verify that the agent correctly reads actual hardware counters:
```powershell
python main.py --test
```

### Step 4: Register Agent with CloudPulse Backend
Obtain an **Agent Registration Token** from the CloudPulse Web Dashboard (Servers -> Register Server), then run:
```powershell
python main.py --register <YOUR_REGISTRATION_TOKEN> --url http://<BACKEND_HOST>:8000 --name "My-Windows-Workstation"
```
This generates credentials and stores them securely in `agent_config.json`.

### Step 5: Start Continuous Monitoring
```powershell
python main.py
```
*(Optional)* Run as a Windows Background Service using Task Scheduler or NSSM (Non-Sucking Service Manager).

---

## 3. Installation on Linux (Ubuntu / Debian / RHEL / CentOS)

### Step 1: Clone and Enter Directory
```bash
git clone <repository_url> cloudpulse
cd cloudpulse/agent
```

### Step 2: Setup Virtual Environment & Install Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Test Telemetry Collection
```bash
python3 main.py --test
```

### Step 4: Register Agent
```bash
python3 main.py --register <YOUR_REGISTRATION_TOKEN> --url http://<BACKEND_HOST>:8000 --name "Production-Ubuntu-Node"
```

### Step 5: Setup systemd Background Service (Production)
Create a service file at `/etc/systemd/system/cloudpulse-agent.service`:

```ini
[Unit]
Description=CloudPulse Host Telemetry Agent
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/cloudpulse/agent
ExecStart=/opt/cloudpulse/agent/venv/bin/python3 /opt/cloudpulse/agent/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable cloudpulse-agent
sudo systemctl start cloudpulse-agent
sudo systemctl status cloudpulse-agent
```

---

## 4. Operational Features

- **Interval:** Metric collection occurs every 5 seconds (customizable with `--interval 10` or in `agent_config.json`).
- **Resilience:** If the backend becomes unreachable, metrics are buffered in an in-memory queue (up to 120 cycles) and automatically transmitted with exponential backoff once connectivity is restored.
- **Heartbeat:** Sends a lightweight health check every 15 seconds.
