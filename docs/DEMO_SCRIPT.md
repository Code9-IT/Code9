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
they can tell which vessels need attention. Notice that **MV Edge Aurora
(IMO9300001)** has the most issues — it has stale and down applications.

---

### 3. Single Vessel Incident Investigation (3-4 minutes)

Navigate to the **UDS Incident Workbench** dashboard. Select vessel
**MV Edge Aurora (IMO9300001)**.

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

Open the **NOC Support** dashboard. Select vessel **MV Edge Aurora (IMO9300001)**.

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

There are two AI analysis paths:

1. **UDS path (preferred for the demo)** — From the **UDS Incident Workbench**
   or **NOC Support** dashboard, click the **AI Analysis** link in the alert
   column. This opens
   `GET /api/v1/uds/analyze/view?vessel=IMO9300001&app=...&alert_name=...&severity=...`
   which is keyed by vessel + app + alert name and persists the result so
   reopening the same alert returns the same analysis.
2. **Legacy telemetry path** — From the **Ship Operations** dashboard, click
   an event row's **Analyze** link to open the legacy
   `/api/v1/analyze/{event_id}/view` page.

**Show**:
- The analysis page with AI-generated text
- Suggested actions
- Confidence label: **Low / Medium / High (model confidence)** — both render
  paths agree on the same label scheme
- The retrieved RAG documents and the tool-call trace (UDS path)
- The model used for analysis

**Talking point**: The AI agent uses RAG-grounded maritime knowledge and MCP
tools to investigate incidents automatically. It retrieves relevant
documentation, calls data query tools to get current metrics and alerts, and
produces an actionable analysis. The confidence label is honest — it says
"model confidence" to make clear this is AI-generated, and uses three plain
buckets instead of a misleading percentage.

---

### 6. AI Chat (2-3 minutes)

Open the **AI Chat** page from the shared dashboard navigation, or directly at
http://localhost:8000/api/v1/chat.

Ask example questions:
- "Which vessels have critical alerts right now?"
- "What happened on IMO9300001 in the last 6 hours?"
- "Which apps are degraded across multiple vessels?"
- "Is alert frequency rising or falling on the fleet right now?"

**Talking point**: Operators can ask natural-language questions and get answers
grounded in real data. The assistant uses the same UDS MCP tool subset that
powers the dashboards, including the predictive `get_alert_trend` tool, so the
answers reflect the actual state of the system. If a tool call fails, the
answer is clearly marked as "live tools failed (answer not grounded)" so the
operator knows not to trust it blindly.

---

### 7. Alert Trends — Predictive Analysis (2 minutes)

Open the **Alert Trends** dashboard from the shared nav, or directly at
http://localhost:3000/d/maritime_alert_trends/alert-trends.

**Show**:
- Alert frequency over time (bar chart with 4-hour buckets, zero-count
  buckets included via the generate_series spine)
- Per-vessel alert breakdown
- Severity distribution stacked chart
- Trend summary table showing RISING / STABLE / FALLING / INSUFFICIENT DATA
  per vessel. The summary honours the dashboard time range and the vessel /
  severity template variables.
- Try changing the vessel filter to one IMO and watch all four panels update.

**Talking point**: Beyond reactive monitoring, the system can detect trends.
If alert frequency is rising on a vessel, that is an early warning before the
situation becomes critical. The `get_alert_trend` MCP tool provides the same
analysis programmatically for the AI agent, including a minimum-sample guard
that returns "insufficient data" instead of pretending statistical noise is a
trend.

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
| MV Edge Aurora | IMO9300001 | Most interesting — has stale and down apps; mapped to the legacy vessel_001 telemetry feed |
| MV Edge Borealis | IMO9300002 | data-quality-processor is degraded |
| MT Nordic Fjord | IMO9300003 | Mostly healthy |

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
