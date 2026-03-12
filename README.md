# Credpanion — Agentic Credit Intelligence Platform

**Credpanion** is a multi-agent AI platform built for hackathons that simulates a bank's credit committee to evaluate corporate loan applications. It replaces human-intensive verification with a deterministic pipeline powered by 8 specialized AI agents.

The system detects carousel fraud, flags inflated revenue, parses legal litigation, validates factory operational reality via images, and finalizes everything into a professional, downloadable `.docx` Credit Appraisal Memo (CAM).

![Architecture](https://via.placeholder.com/800x400.png?text=Credpanion+Architecture)

## Features
- **Deterministic Multi-Agent Committee:** Agents independently vote with rationales (Auditor, Sleuth, Vision, Adversarial).
- **Forensic Network Fraud Detection:** Finds hidden loops in arbitrary transaction networks via graph logic (PyVis/vis-network).
- **Operational Reality Check:** Analyzes provided factory images to compute an "Operational Utilization" score that triggers automatic rejections if under 50%.
- **Counterfactual Scenarios:** Performs SHAP-style what-if sensitivity analysis, calculating risk scores *if* certain flags were resolved.
- **Premium Next.js Dashboard:** Hackathon-ready beautiful dark-mode UI with a live agent transcript, SVG risk gauges, and dynamic charts.

---

## 🚀 Quick Start (One-Click)

The easiest way to run the full stack (Backend on `8000`, Frontend on `3000`) is:
- **Windows:** Double-click `start.bat`
- **Linux / Mac:** Run `./start.sh`

---

## 🐳 Docker Deployment (Production Ready)

To spin up the entire application inside isolated containers, simply run:
```bash
docker-compose up --build
```
The Next.js dashboard will be available at [http://localhost:3000](http://localhost:3000).
The OpenAPI docs will be available at [http://localhost:8000/docs](http://localhost:8000/docs).

---

## 🛠 Manual Installation

### 1. Backend (FastAPI / LangGraph)
Requires Python 3.10+.
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Run the backend
uvicorn backend.main:app --reload --port 8000
```

### 2. Frontend (Next.js)
Requires Node 18+.
```bash
cd frontend-next
npm install
npm run dev
# Go to http://localhost:3000
```

---

## 🤖 The 8-Agent Pipeline

1. `ExtractorAgent` — Structurally parses GST + Bank PDFs.
2. `AuditorAgent` — Cross-references GST sales against Bank credits to detect inflation.
3. `SleuthAgent` — Searches simulated judicial records for Section 138 (Cheque Bounce) or labor disputes.
4. `VisionAgent` — Evaluates uploaded machinery photos for active vs. idle assets.
5. `AdversarialAgent` — Dedicated "red teamer" looking for direct transaction loops (Carousel fraud).
6. `CommitteeVote` — Weighs individual agent scores against a global 0.7 approval threshold.
7. `RiskEngine` — Computes base score minus exact penalties.
8. `CamGenerator` — Compiles findings into a structured Word document.

---

## 📡 Core API Routes (port 8000)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/analyze` | POST | Triggers the full agent pipeline. Returns the state dict. |
| `/graph` | GET | PyVis transaction graph. |
| `/risk` | GET | Deterministic risk scores and committee vote breakdown. |
| `/report` | GET | Downloadable CAM .docx file. |
| `/health` | GET | Simple ok status check. |

---

## Demo Profiles

Select these from the dashboard sidebar to instantly mock different scenarios:

*   **CleanCorp:** Healthy borrower. Clean tax records, active factory. Passes easily.
*   **FraudCo:** Fails due to hard blocks. Engages in circular trading with dummy entities, heavily inflates revenue, and has a predominantly idle factory.
*   **LitigationLtd:** Medium/High risk. Shows Section 138 litigations and lower base scores. Often rejected by committee vote threshold.
