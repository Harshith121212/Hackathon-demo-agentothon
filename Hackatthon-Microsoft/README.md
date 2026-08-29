# 🚢 Maritime Operations Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Pydantic](https://img.shields.io/badge/Pydantic-v2-E92063.svg?style=flat&logo=pydantic&logoColor=white)](https://docs.pydantic.dev)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> **Continuously monitor a shipping fleet against changing external conditions, deterministically determine which voyages are exposed to meaningful risk, investigate the operational/business consequences with internal ERP context, and give management actionable intelligence—with humans approving consequential communications.**

---

## 🧭 The Core Problem & Philosophy

Global container and bulk carriers face dynamic oceanic disruptions: severe typhoons, security conflicts in strategic straits, and port congestion. Modern operators are overwhelmed with disjointed alerts.

This platform adheres to three key engineering principles:
1. **Deterministic Spatiotemporal Computation for Physical Risk**: Trajectory projections, great-circle waypoint interpolation, and weather grid intersections are computed deterministically (spherical mathematics, not probabilistic LLMs).
2. **Fleet-Scale Multi-Tier Filtering**: $O(N)$ coarse bounding-box spatial indexing filters 95%+ of unaffected ships in $<0.5\text{ms}$. Only high-exposure candidate vessels trigger fine-grained math, and only significant threats trigger AI investigations.
3. **Multi-Disciplinary Business Impact Analysis with Human Gate**: When a severe risk is detected, the **AI Investigation Agent** queries simulated **Maritime ERP systems** (Customer SLAs, cargo valuations, crew duty caps, visa deadlines, drydock shipyard bookings, and berth reservations) to determine true financial and operational consequences. Draft communications are generated, and **strict human operator approval** is enforced before dispatch.

---

## 🏛️ System Architecture

```
                         ┌─────────────────────────────────┐
                         │   External World & Ingestion    │
                         │ AIS Telemetry • Weather • Zones │
                         └───────────────┬─────────────────┘
                                         │
                                         ▼
                         ┌─────────────────────────────────┐
                         │      Normalization Layer        │
                         │ Canonical Pydantic Domain Model │
                         └───────────────┬─────────────────┘
                                         │
                                         ▼
                         ┌─────────────────────────────────┐
                         │ Deterministic Projection Engine │
                         │ Spherical Great-Circle Math     │
                         └───────────────┬─────────────────┘
                                         │
                                         ▼
                         ┌─────────────────────────────────┐
                         │      Risk & Exposure Engine     │
                         │ Spatiotemporal Route Matching   │
                         └───────────────┬─────────────────┘
                                         │
                                 Significant Risk?
                                 /               \
                               NO                 YES
                               │                   │
                               ▼                   ▼
                         Normal Fleet     AI Investigation Agent
                         Status Feed               │
                                                   ▼
                                         Maritime ERP Reasoning
                                    (SLAs • Crew • Drydock • Berths)
                                                   │
                                                   ▼
                                         Management Risk Brief
                                                   │
                                    ┌──────────────┴──────────────┐
                                    ▼                             ▼
                            Interactive Map &            Human Action Gate
                               Risk Queue              (Approve / Edit / Reject)
```

---

## 🚀 Quickstart & Local Run

### Prerequisites
- Python 3.11+
- Virtual Environment or Docker

### 1. Local Setup
```bash
# Clone and enter directory
cd Hackatthon-Microsoft

# Activate Python virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt

# Start application
python3 -m backend.app.main
```

Open your browser to: **`http://localhost:8000`**

### 2. Run Automated Test Suite
```bash
source .venv/bin/activate
PYTHONPATH=. pytest -v backend/tests/
```

### 3. Docker Launch
```bash
docker compose -f deploy/docker-compose.yml up --build
```

---

## 🎬 1-Click Hackathon Demo Flow

1. **Baseline State**:
   - The fleet displays 50 global merchant vessels operating in nominal conditions across Atlantic, Pacific, and Indian Ocean trade corridors.
   - Filter latency displays $\approx 0.45\text{ms}$.
2. **Trigger Typhoon Malakas Scenario**:
   - Click **`⚡ Typhoon Malakas (OS-104)`** in the top navigation bar.
   - The system injects a Force-12 violent cyclonic storm ($9.2\text{m}$ waves, $64\text{kts}$ winds) into the Andaman Sea / Bay of Bengal gateway.
   - The deterministic spatiotemporal filter instantly evaluates the 50 vessels, flags vessel **Ocean Star (`VSL-OS-104`)** as 🔴 **`CRITICAL`**, and projects an estimated $\approx 36\text{-hour}$ weather delay.
3. **AI Multi-Disciplinary Investigation**:
   - Click **`[View Investigation]`** on Ocean Star.
   - Inspect the **Agent Tool Execution & Reasoning Trace**:
     - *Tool 1: `get_vessel_details`* $\rightarrow$ certified wave limit $6.0\text{m}$.
     - *Tool 2: `get_weather_exposure`* $\rightarrow$ $9.2\text{m}$ waves intersecting corridor ($18:00 - 23:00\text{ UTC}$).
     - *Tool 3: `get_customer_sla`* $\rightarrow$ **Acme Logistics Global** (\$42.5M Semiconductor Cargo), $\$85,000/\text{day}$ delay penalty, contractual 24h advance notice requirement.
     - *Tool 4: `get_crew_schedule`* $\rightarrow$ 4 senior officers Schengen visas expire at Rotterdam in 40h; delay causes immigration non-compliance.
     - *Tool 5: `get_maintenance_schedule`* $\rightarrow$ Damen Shiprepair Rotterdam Yard 4 drydock slot standby demurrage ($\$28,000/\text{day}$).
     - *Tool 6: `get_port_congestion`* $\rightarrow$ Rotterdam Maasvlakte II congestion & pilot reservation window.
4. **Human-in-the-Loop Action Approval**:
   - Click **`[Review & Authorize Draft Actions]`** to navigate to the **Action Center**.
   - Review the tailored executive memo drafted by the AI for Acme Logistics VP Victoria Lindqvist.
   - Use **`[Edit Message]`** to customize terms or click **`[Authorize & Dispatch]`**.
   - Notice the live update to the **Immutable Event Audit Trail**.
5. **Observability & Scale Tab**:
   - Switch to the **Observability & Scale** tab to review the 4-stage pipeline funnel showing sub-millisecond filtering and throughput efficiency.

---

## 📦 Directory Structure

```
├── backend/
│   ├── app/
│   │   ├── core/                  # Canonical Pydantic v2 domain models & config
│   │   ├── adapters/              # AIS, Weather & Incident provider protocols
│   │   ├── engine/                # Trajectory projection, spatiotemporal matching, risk engine
│   │   ├── erp/                   # Simulated Maritime ERP database (SLAs, Crew, Drydock)
│   │   ├── agent/                 # AI Investigation Agent, Tool Suite & Brief generator
│   │   ├── events/                # Event dispatcher, scenarios & WebSocket broadcaster
│   │   ├── observability/         # Observability metrics & latency accounting
│   │   ├── api/                   # FastAPI REST routes
│   │   └── main.py                # App entrypoint & static frontend mounting
│   ├── tests/                     # Comprehensive pytest test suite
│   └── requirements.txt
├── frontend/
│   ├── index.html                 # Dark nautical command center UI
│   └── static/
│       ├── css/style.css          # Design system, marker animations, glowing rings
│       └── js/
│           ├── map.js             # Leaflet map, vessel headings, storm overlays
│           ├── agent_view.js      # Structured brief rendering & reasoning traces
│           ├── actions.js         # Human action approval, editing & audit log
│           ├── metrics.js         # Observability funnel & latency counters
│           └── app.js             # State controller & WebSocket manager
├── deploy/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── azure-container-apps.bicep
├── .env.example
└── README.md
```

---

## ☁️ Azure Cloud Architecture Blueprint

The platform is designed for enterprise Azure deployment:
- **Azure Container Apps**: Serverless scaling for FastAPI backend and ingestion workers.
- **Azure Database for PostgreSQL**: Relational store for historical AIS tracks and voyage ledger.
- **Azure Service Bus**: Asynchronous event queue for incoming AIS/weather telemetry bulletins.
- **Azure OpenAI Service**: Model deployment for AI Investigation reasoning loops.
- **Application Insights**: Distributed tracing, latency telemetry, and SLA alerting.

---

## 📄 License
MIT License. Built for the Microsoft Maritime AI Hackathon.
