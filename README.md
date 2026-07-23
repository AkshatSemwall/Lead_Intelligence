# Lead Intelligence — Autonomous Multi-Agent System

![Lead Intelligence System Architecture](https://img.shields.io/badge/Architecture-LangGraph%20%2B%20FastAPI%20%2B%20React-0ea5e9?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

An autonomous multi-agent system that automatically researches a company after a lead submits a form, generates a personalized business audit report, converts it into a professional PDF using WeasyPrint, emails it to the prospect via Gmail API, logs the execution, stores lead information in Google Sheets, and archives the generated PDF in Google Drive.

---

## ⚡ Workflow Architecture

```
Lead Form Submission
       ↓
1. Orchestrator Agent       (Initialises state, tracks progress)
       ↓
2. Validation Agent         (Validates inputs, detects test data & duplicates)
       ↓
3. Company Research Agent   (Firecrawl crawl + Tavily multi-query search + LLM extraction)
       ↓
4. Business Analysis Agent  (SWOT, pain points, market position, revenue model)
       ↓
5. Insight Generation Agent (Website audit scoring, automation opportunities, priority actions)
       ↓
6. Report Generation Agent (Composes comprehensive Markdown consulting report)
       ↓
7. PDF Generation Agent    (WeasyPrint conversion with custom executive CSS typography)
       ↓
8. Google Drive Agent      (Uploads PDF, sets public reader permissions, returns URL)
       ↓
9. Email Agent             (Sends HTML email with PDF attachment via Gmail API)
       ↓
10. Logging Agent          (Saves structured execution JSON logs)
       ↓
11. Google Sheets Agent    (Appends lead details, timestamp, PDF & email status)
       ↓
Finalise & Complete
```

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Frontend** | React, Tailwind CSS v4, Lucide React, Axios, React Router v6 |
| **Backend** | FastAPI (Async), Pydantic v2, Uvicorn |
| **Agent Framework** | LangGraph (`StateGraph` with retry wrappers & conditional edges) |
| **LLM Provider** | Gemini 1.5 Pro (default), pluggable architecture for Claude & GPT-4o |
| **Research Tools** | Tavily Search API, Firecrawl Web Scraping & Crawling |
| **Document Processing**| WeasyPrint (HTML/CSS to PDF) |
| **Email Delivery** | Gmail API (OAuth2 Refresh Token Flow) |
| **Storage & Logging** | Google Sheets API, Google Drive API |
| **Deployment** | Docker (Multi-stage build), Docker Compose |

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 20+
- `cairo` and `pango` system libraries (for WeasyPrint PDF generation)

---

### Step 1: Clone & Configure Environment

```bash
git clone https://github.com/AkshatSemwall/Lead_Intelligence.git
cd Lead_Intelligence
```

Create a `.env` file in the project root and add your API keys and credentials:
- `GEMINI_API_KEY`
- `TAVILY_API_KEY`
- `FIRECRAWL_API_KEY`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `GOOGLE_REFRESH_TOKEN`
- `GOOGLE_SHEET_ID`, `GOOGLE_DRIVE_FOLDER_ID`, `GMAIL_SENDER_EMAIL`

> Keep your `.env` file local and do not commit real secrets to source control.

---

### Step 2: Run via Docker Compose (Recommended)

```bash
docker-compose up --build
```
Access the application at: **`http://localhost:8000`**

---

### Step 3: Run Locally (Development Mode)

#### 1. Backend Setup
```bash
# Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate  # On macOS/Linux: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
uvicorn backend.main:app --reload --port 8000
```

#### 2. Verify the installation
```bash
pytest -q
```

#### 2. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Access Vite dev server at **`http://localhost:5173`** (proxies `/api` requests to backend at `:8000`).

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/submit-lead` | Submit lead form & trigger background workflow |
| `GET` | `/api/workflow-status/{id}` | Query real-time workflow status and node execution |
| `GET` | `/api/report/{id}` | Retrieve generated Markdown report & Drive/PDF links |
| `GET` | `/api/report/{id}/pdf` | Download generated PDF document |
| `GET` | `/api/logs/{id}` | Retrieve full structured execution log |
| `GET` | `/api/workflows` | List all submitted lead workflows |
| `GET` | `/api/health` | Service health status |

---

## 📁 Repository Structure

```
Lead_Intelligence/
├── backend/
│   ├── main.py               # FastAPI entrypoint & CORS configuration
│   ├── config.py             # Pydantic settings loading from .env
│   ├── agents/               # 11 Dedicated Agent Node implementations
│   │   ├── validation.py
│   │   ├── company_research.py
│   │   ├── business_analysis.py
│   │   ├── insight_generation.py
│   │   ├── report_generation.py
│   │   ├── pdf_generation.py
│   │   ├── email_agent.py
│   │   ├── logging_agent.py
│   │   ├── sheets_agent.py
│   │   └── drive_agent.py
│   ├── graph/
│   │   └── workflow.py       # LangGraph StateGraph orchestration definition
│   ├── services/             # Integrations (LLM, Tavily, Firecrawl, WeasyPrint, Gmail, Sheets, Drive)
│   ├── prompts/              # Centralised LLM prompt templates
│   ├── models/               # Pydantic data models & LangGraph TypedDict state
│   ├── utils/                # Helpers, JSON extractors, retry logic & structured logging
│   └── api/                  # FastAPI routers and in-memory state store
├── frontend/
│   ├── src/
│   │   ├── pages/            # LeadForm, WorkflowStatus, ReportPage, LogsPage, DashboardPage
│   │   ├── api/              # Axios HTTP client
│   │   ├── App.jsx           # React router setup
│   │   └── index.css         # Glassmorphism & dark theme styles
│   └── vite.config.js
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔒 Code Quality & Verification

- **Type Hints & Validation**: Pydantic models for all API requests and state transfers.
- **Async Execution**: Non-blocking background task processing for LangGraph workflows.
- **Error Handling**: Graceful fallback data generation for research/analysis nodes to ensure pipeline completion.
- **Retry Logic**: Automatic exponential backoff retry wrapper on external API calls.
- **Runtime Hardening**: Request ID and security headers, durable workflow persistence, and regression tests for core middleware behavior.
