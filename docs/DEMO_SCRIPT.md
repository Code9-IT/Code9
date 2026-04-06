# Demo Script

Step-by-step guide for demonstrating the Maritime Agentic Observability platform.
Designed for the Kartverket presentation and Knowit stakeholder demos.

## Before the Demo

### Start the stack (do this 10-15 minutes before)

```bash
docker compose down -v
docker compose up -d --build
```

### Wait for data

```bash
docker compose logs -f uds-seeder
```

Wait for `Backfill complete` — this means 6 hours of historical data is loaded.

### Verify services

- Grafana: http://localhost:3000 (admin / code9-demo-admin)
- Agent API: http://localhost:8000/docs
- MCP API: http://localhost:8001/docs

### Pre-warm the LLM (optional, reduces first-analysis wait)

Open http://localhost:8000/docs and send a quick test request to the analyze
endpoint so Ollama loads the model into memory.

---

## Demo Flow

### 1. Introduction — The Problem (1-2 minutes)

**Talking point**: Maritime vessels run multiple applications that produce
metrics, alerts, and logs. When something goes wrong, operators at the NOC
(Network Operations Center) need to quickly understand what is happening across
the fleet, investigate individual vessels, and decide on actions.

Open **Grafana** at http://localhost:3000.

---

### 2. Fleet Overview (2-3 minutes)

Open the **Fleet Overview** dashboard.

**Show**:
- All 3 vessels with their operational status
- Color-coded status: healthy (green), degraded (yellow), critical (red)
- Active alert counts per vessel

**Talking point**: This is the first thing a NOC operator sees. At a glance
they can tell which vessels need attention. Notice that IMO9300001 has the most
issues — it has stale and down applications.

---

### 3. Single Vessel Incident Investigation (3-4 minutes)

Navigate to the **UDS Monitoring** dashboard. Select vessel **IMO9300001**.

**Show**:
- Application health overview — some apps are healthy, some degraded or critical
- Active alerts with severity and timestamps
- Metric history showing trends
- Application logs for context

**Talking point**: When a vessel shows problems, the operator drills into this
view. They can see exactly which apps are affected, what alerts are firing, and
the recent history. This directly addresses User Story 1 — single vessel
incident investigation.

---

### 4. NOC Support Investigation (2-3 minutes)

Open the **NOC Support** dashboard. Select vessel **IMO9300001**.

**Show**:
- Full operational snapshot
- Incident timeline (chronological alerts + logs)
- Connectivity status

**Talking point**: When a support ticket comes in, this dashboard gives the
full picture. The timeline shows what happened in order, and the operational
snapshot provides everything needed to respond to the ticket.

---

### 5. AI Analysis (3-4 minutes)

**This is the core "agentic observability" demo.**

From the UDS Monitoring or NOC Support dashboard, click an alert row to trigger
an AI analysis (if Task 1 is complete). Otherwise, demonstrate via the legacy
path:

1. Go to **Ship Operations** dashboard
2. Click an event to open the AI analysis page

**Show**:
- The analysis page with AI-generated text
- Suggested actions
- Confidence level (Low / Medium / High — clearly labeled as model confidence)
- The model used for analysis

**Talking point**: The AI agent uses RAG-grounded maritime knowledge and MCP
tools to investigate incidents automatically. It retrieves relevant
documentation, calls data query tools to get current metrics and alerts, and
produces an actionable analysis. The confidence label is honest — it says
"model confidence" to make clear this is AI-generated.

---

### 6. AI Chat (2-3 minutes)

*If Task 2 is complete:*

Open the **AI Chat** page (linked from dashboard navigation).

Ask example questions:
- "Which vessels have critical alerts right now?"
- "What happened on IMO9300001 in the last 6 hours?"
- "Which app is degraded across multiple vessels?"

**Talking point**: Operators can ask natural-language questions and get answers
grounded in real data. The assistant uses the same MCP tools that power the
dashboards, so the answers reflect the actual state of the system.

---

### 7. Alert Trends — Predictive Analysis (2 minutes)

Open the **Alert Trends** dashboard.

**Show**:
- Alert frequency over time (bar chart with 4-hour buckets)
- Per-vessel alert breakdown
- Severity distribution stacked chart
- Trend summary table showing RISING / STABLE / FALLING per vessel

**Talking point**: Beyond reactive monitoring, the system can detect trends.
If alert frequency is rising on a vessel, that is an early warning before the
situation becomes critical. The `get_alert_trend` MCP tool provides the same
analysis programmatically for the AI agent.

---

### 8. Cross-Vessel Correlation (1-2 minutes)

Show MCP tool output (via Agent API at http://localhost:8000/docs or through
the chat if available):

Call `get_cross_vessel_correlation` to show applications and alert types
affecting multiple vessels simultaneously.

**Talking point**: When the same problem appears on multiple vessels, it often
points to a systemic issue — a bad software update, a shared infrastructure
problem, or a common configuration error. This tool surfaces those patterns
automatically.

---

### 9. Architecture Overview (1-2 minutes)

**Talking point**: The system uses:
- **PostgreSQL + TimescaleDB** for time-series data
- **pgvector** for RAG document retrieval
- **Grafana** for visualization
- **FastAPI** for the agent and MCP services
- **Ollama** running llama3.2 locally for AI analysis
- **Docker Compose** for orchestration — one command to start everything

All 13 MCP tools are exposed as a REST API that the AI agent calls during
analysis. The RAG knowledge base contains 17 maritime reference documents.

---

## Key Demo Vessels

| Vessel | IMO | Characteristics |
|--------|-----|----------------|
| North Sea Explorer | IMO9300001 | Most interesting — has stale and down apps |
| Baltic Carrier | IMO9300002 | data-quality-processor is degraded |
| Atlantic Pioneer | IMO9300003 | Mostly healthy |

The `data-quality-processor` app is deliberately degraded on both IMO9300001
and IMO9300002 to demonstrate cross-vessel correlation.

## FAQ for Audience Questions

**Q: Why use a local LLM instead of a cloud API?**
A: Maritime vessels may have limited or expensive connectivity. A local model
works offline and avoids sending operational data to external services.

**Q: Is the data real?**
A: The data is synthetic but modeled on realistic maritime scenarios. The seed
data uses deterministic scenario flags to create believable situations.

**Q: How does the AI know about maritime systems?**
A: The RAG knowledge base in `docs/knowledge/` contains 17 reference documents
covering engines, sensors, alarm types, troubleshooting procedures, and
maritime regulations. These are retrieved based on relevance to each incident.

**Q: Can this scale to more vessels?**
A: The architecture supports it. Adding vessels means adding rows to the
reference data and adjusting the seeder. The dashboards and MCP tools are
already parameterized by vessel.
