# CloudPulse – Enterprise Cloud Infrastructure Monitor & Performance Tuning Profiler

[![Python Version](https://img.shields.io/badge/python-3.11%20%7C%203.12%20%7C%203.13-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB.svg)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4-blue.svg)](https://www.typescriptlang.org/)
[![Scikit-Learn](https://img.shields.io/badge/ML-Isolation%20Forest-orange.svg)](https://scikit-learn.org/)
[![Tests](https://img.shields.io/badge/PyTest-30%20Passed-brightgreen.svg)]()

> **B.Tech Computer Science & Engineering Capstone Project | Session 2026–2027**  
> An enterprise-grade, distributed infrastructure monitoring platform with authentic telemetry, Scikit-learn anomaly detection, intelligent deduplicating alerts, runtime code profiling, and real-time WebSockets.

---

## 🌟 Key Capabilities

- **Authentic Telemetry (No Mock Data):** The Python agent directly extracts hardware telemetry via `psutil`, `platform`, and `socket` (per-core CPU, RAM breakdown, disk partition I/O, network upload/download bandwidth speed, and top 10 CPU/RAM processes).
- **Multi-Server Fleet Management:** Provision and register Windows machines, Linux nodes, or Cloud VMs with unique, revocable cryptographic tokens.
- **Intelligent Alert Engine with Deduplication:** Dynamic threshold evaluation for CPU, RAM, and Disk without alert flooding; state-aware transition (Active $\rightarrow$ Acknowledged $\rightarrow$ Resolved) and auto-recovery.
- **Machine Learning Anomaly Detection:** Scikit-learn **Isolation Forest** trained on historical multi-server metrics, tracking first-order differences (trends) with metric attribution and transparent cold-start safety.
- **Performance Tuning Profiler:** Subsystem bottleneck detection, non-destructive recommendations, and Python execution timing decorators using `cProfile` and `time.perf_counter`.
- **Multi-Tenant Organization Isolation:** Complete tenant boundaries protecting server telemetry across distinct organizations.
- **Real-Time WebSockets:** Live metric streams push updates directly into the React TypeScript SaaS dashboard.
- **Executive Audit Reports:** Downloadable statistical summaries in CSV and audit-ready binary PDF formats (generated via ReportLab).
- **Tested & Verified:** Comprehensive test suite of **30 PyTest tests** covering agents, APIs, database, ML, profiler, and security.

---

## 🏗️ System Architecture

```
+-------------------------------------------------------------------+
|                       Target Host Machines                        |
|                                                                   |
|   +-----------------------------------------------------------+   |
|   |                   CloudPulse Agent (Python)               |   |
|   |  - SystemCollector (psutil, platform, socket)             |   |
|   |  - ProcessCollector (Top 10 CPU & Memory Safe Iterator)   |   |
|   |  - MetricSender (In-Memory Deque Queue + Exp Backoff)     |   |
|   +-----------------------------------------------------------+   |
+---------------------------------+---------------------------------+
                                  |
                   Authenticated HTTPS / Agent Token
                                  v
+-------------------------------------------------------------------+
|                     FastAPI Backend Server                        |
|                                                                   |
|  [Auth & RBAC]         [Server Registry]     [Ingestion Pipeline] |
|  [Alert Engine]        [Isolation Forest]    [Profiler Service]   |
|  [Report Service]      [WebSocket Stream]    [Alembic / Engine]   |
+---------------------------------+---------------------------------+
                                  |
                                  v
+---------------------------------+---------------------------------+
|                Persistence & Visualization Layer                  |
|                                                                   |
|  - PostgreSQL / SQLite Database (12 Normalized Indexed Tables)    |
|  - React 18 TypeScript Dashboard (Tailwind CSS, Recharts, Vite)   |
|  - WebSocket Client (Instant Telemetry Updates)                   |
+-------------------------------------------------------------------+
```

---

## 🚀 Quick Start Guide (Windows / Linux)

### 1. Prerequisites
- **Python:** 3.10, 3.11, 3.12, or 3.13
- **Node.js:** v18+ or v20+ with npm

### 2. Backend Setup
1. Clone the repository and navigate to the project root:
   ```bash
   cd "s:/python project"
   ```
2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```
3. Initialize the database and launch the backend:
   ```bash
   python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```
   *The backend will automatically initialize all 12 database tables and serve both the REST API, WebSockets, and built frontend on `http://127.0.0.1:8000`!*
   - Interactive API Docs: `http://127.0.0.1:8000/docs`

---

### 3. Frontend Development (Optional for Live Editing)
If you wish to modify the React frontend with Vite Hot Module Replacement:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

### 4. Running the Host Monitoring Agent
To monitor your host machine:

1. Test local hardware collection without sending:
   ```bash
   python -m agent.main --test
   ```
2. Register the agent with the running backend:
   - Navigate to the Web Dashboard (`http://127.0.0.1:8000`)
   - Log in with default admin credentials:
     - **Email:** `admin@cloudpulse.io`
     - **Password:** `CloudPulsePassword2026!`
   - Go to **Server Fleet** $\rightarrow$ Click **Register New Server**
   - Copy the generated registration command or execute:
     ```bash
     python -m agent.main --register <YOUR_REGISTRATION_TOKEN> --url http://127.0.0.1:8000 --name "My-Workstation"
     ```
3. Start streaming live metrics:
   ```bash
   python -m agent.main
   ```

---

## 🧪 Running PyTest Test Suite

Run all 30 tests with verbose output:
```bash
python -m pytest backend/tests -v
```

Expected output:
```
backend/tests/test_agent_collector.py::test_cpu_collection PASSED        [  3%]
backend/tests/test_agent_collector.py::test_memory_collection PASSED     [  6%]
backend/tests/test_agent_collector.py::test_disk_collection PASSED       [ 10%]
backend/tests/test_agent_collector.py::test_network_calculations PASSED  [ 13%]
backend/tests/test_agent_collector.py::test_process_collector PASSED     [ 16%]
backend/tests/test_alerts.py::test_alert_generation_and_deduplication PASSED [ 20%]
backend/tests/test_alerts.py::test_alert_acknowledge_and_resolve PASSED  [ 23%]
backend/tests/test_anomaly_ml.py::test_anomaly_model_cold_start_handling PASSED [ 26%]
backend/tests/test_anomaly_ml.py::test_anomaly_model_training_and_detection PASSED [ 30%]
backend/tests/test_auth_api.py::test_user_registration_success PASSED    [ 33%]
backend/tests/test_auth_api.py::test_user_registration_duplicate_email PASSED [ 36%]
backend/tests/test_auth_api.py::test_user_login_success PASSED           [ 40%]
backend/tests/test_auth_api.py::test_user_login_invalid_password PASSED  [ 43%]
backend/tests/test_auth_api.py::test_auth_me_endpoint PASSED             [ 46%]
backend/tests/test_auth_api.py::test_refresh_token_flow PASSED           [ 50%]
backend/tests/test_metrics_api.py::test_metric_ingestion_success PASSED  [ 53%]
backend/tests/test_metrics_api.py::test_metric_ingestion_unauthenticated PASSED [ 56%]
backend/tests/test_metrics_api.py::test_metric_retrieval PASSED          [ 60%]
backend/tests/test_profiler_reports.py::test_profiler_decorator PASSED   [ 63%]
backend/tests/test_profiler_reports.py::test_server_profiler_endpoint PASSED [ 66%]
backend/tests/test_profiler_reports.py::test_daily_and_weekly_reports PASSED [ 70%]
backend/tests/test_profiler_reports.py::test_csv_export PASSED           [ 73%]
backend/tests/test_profiler_reports.py::test_pdf_export PASSED           [ 76%]
backend/tests/test_servers_api.py::test_create_server_slot PASSED        [ 80%]
backend/tests/test_servers_api.py::test_agent_registration_flow PASSED   [ 83%]
backend/tests/test_servers_api.py::test_agent_registration_invalid_token PASSED [ 86%]
backend/tests/test_servers_api.py::test_agent_heartbeat PASSED           [ 90%]
backend/tests/test_servers_api.py::test_offline_detection PASSED         [ 93%]
backend/tests/test_tenant_isolation.py::test_cross_organization_data_isolation PASSED [ 96%]
backend/tests/test_tenant_isolation.py::test_agent_token_revocation PASSED [100%]

======================= 30 passed in 15.07s =======================
```

---

## 🐳 Docker Deployment

To launch the full production environment with PostgreSQL and multi-stage Nginx:
```bash
docker-compose up --build -d
```
- Frontend UI: `http://localhost:3000`
- FastAPI Backend: `http://localhost:8000`
- PostgreSQL: Port `5432`

---

## 📡 API Reference Overview

| HTTP Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/api/auth/register` | Register new admin account & organization |
| `POST` | `/api/auth/login` | Authenticate credentials & issue JWT access/refresh tokens |
| `GET` | `/api/auth/me` | Retrieve profile of authenticated user |
| `GET` | `/api/servers` | List registered fleet nodes with live health status |
| `POST` | `/api/servers` | Provision server slot & generate registration token |
| `GET` | `/api/servers/{id}` | Retrieve individual server hardware profile & metrics |
| `POST` | `/api/agent/register` | Agent pairs with backend using registration token |
| `POST` | `/api/agent/metrics` | Ingest real-time telemetry from authenticated agent |
| `POST` | `/api/agent/heartbeat` | Lightweight node heartbeat ping |
| `GET` | `/api/metrics/latest` | Most recent telemetry across all servers |
| `GET` | `/api/metrics/history` | Historical time-series points for charting |
| `GET` | `/api/alerts` | List incidents with active/acknowledged/resolved filter |
| `PUT` | `/api/alerts/{id}/acknowledge` | Acknowledge active incident |
| `PUT` | `/api/alerts/{id}/resolve` | Mark incident as resolved |
| `GET` | `/api/ai/model-status` | Check Isolation Forest training status |
| `POST` | `/api/ai/train` | Train Isolation Forest on historical telemetry |
| `GET` | `/api/ai/anomalies` | Query detected multidimensional outlier records |
| `GET` | `/api/profiler/server/{id}` | Run bottleneck detection & tuning advice |
| `GET` | `/api/reports/daily` | 24-hour executive performance summary |
| `GET` | `/api/reports/weekly` | 7-day executive performance summary |
| `GET` | `/api/reports/export` | Download audit data as `.csv` or binary `.pdf` |
| `WS` | `/ws` | Real-time WebSocket telemetry event stream |

---

## 📜 Project Structure

```
cloudpulse/
├── backend/
│   ├── app/
│   │   ├── api/endpoints/    # REST API endpoints (auth, servers, agent, etc.)
│   │   ├── core/             # JWT, bcrypt security & pydantic configuration
│   │   ├── database/         # SQLAlchemy session & SQLite/Postgres engine
│   │   ├── ml/               # Scikit-learn Isolation Forest anomaly engine
│   │   ├── models/           # 12 SQLAlchemy models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Alert engine, profiler, reports, AWS service
│   │   ├── websocket/        # Real-time WebSocket connection manager
│   │   └── main.py           # FastAPI entry point & SPA static file serving
│   ├── tests/                # 30 Comprehensive PyTest test cases
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── hooks/            # useWebSocket hook
│   │   ├── layouts/          # DashboardLayout with live status badge
│   │   ├── pages/            # Overview, Servers, ServerDetail, Alerts, etc.
│   │   ├── services/         # Axios API client
│   │   ├── types/            # TypeScript data interfaces
│   │   ├── App.tsx           # React Router configuration
│   │   └── main.tsx
│   ├── package.json
│   ├── vite.config.ts
│   └── Dockerfile
├── agent/
│   ├── collector/            # psutil hardware & process telemetry collectors
│   ├── transport/            # HTTPS transport, local deque queue & auth
│   ├── config/               # Agent configuration settings
│   ├── main.py               # Agent CLI & collection loop
│   └── requirements.txt
├── docs/
│   ├── AGENT_INSTALLATION.md     # Installation guide for Windows & Linux
│   └── CAPSTONE_PROJECT_REPORT.md# Complete 22-section academic project report
├── scripts/
│   └── verify_agent_connection.py# End-to-end Phase 4 integration verification
├── docker-compose.yml
├── .env.example
├── .gitignore
└── README.md
```

---

## 🎓 Academic Capstone Submission Information

- **Degree:** B.Tech Computer Science & Engineering (Session 2026–2027)
- **Course:** Advanced Python Capstone Project
- **Official Documentation:** See [docs/CAPSTONE_PROJECT_REPORT.md](docs/CAPSTONE_PROJECT_REPORT.md) for the complete 22-section project report including research papers, mathematical formulas, algorithms, flowchart diagrams, and benchmark results.



<-------------------------------------------------------------------Execution Steps---------------------------------->
Step 1: Open PowerShell / Command Prompt
Open your terminal and navigate to the project directory:
powershell
cd "s:\python project"


Step 2: Start the Backend Server (Terminal 1)
Run the FastAPI backend server:
powershell
python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
Note: The backend automatically serves both the FastAPI REST API and the React production dashboard from http://127.0.0.1:8000.



Step 3: Open the Web Dashboard in Your Browser
Open Chrome, Brave, Edge, or Firefox and go to: 👉 http://127.0.0.1:8000
Log in with your administrator account:
Email: admin@cloudpulse.io
Password: CloudPulsePassword2026!
(You can also click "Create an account" to register a new organization).



Step 4: Start the Host Monitoring Agent (Terminal 2)
Open a second PowerShell window, navigate to s:\python project, and run:
powershell
python -m agent.main
You will see the agent start collecting real hardware metrics and transmitting them every 5 seconds:
[CloudPulse-Agent] CloudPulse Agent started (Server ID: dec8e8b3eff745b492dad5c633a4d820).
[CloudPulse-Agent] Metric sent - CPU: 49.0% | RAM: 87.9% | Disk: 53.9% | Net: Active