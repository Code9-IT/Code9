"""
Validation endpoints for empirical RAG and analysis-quality checks.
These routes do not enable auto-analysis and do not persist analysis runs.
"""

import os

from fastapi.responses import HTMLResponse
from fastapi import APIRouter, HTTPException

from db import get_pool
from models import (
    AnalysisQualityFactors,
    AnalysisValidationRequest,
    AnalysisValidationResponse,
    EventSchema,
    RetrievedDocument,
    RetrievalValidationCase,
    RetrievalValidationCaseResult,
    RetrievalValidationRequest,
    RetrievalValidationResponse,
    ToolCallTrace,
)
from rag.client import (
    RAG_MIN_SIMILARITY,
    RAG_TOP_K,
    retrieve_context_for_query,
)
from routes.analyze import QUICK_ANALYSIS_TOP_K, run_quick_analysis_pipeline

router = APIRouter(tags=["validation"])
VALIDATION_MODEL = os.getenv("OLLAMA_VALIDATION_MODEL", "").strip()


@router.get("/validate/dashboard", response_class=HTMLResponse)
async def validation_dashboard():
    """Simple internal dashboard for retrieval and analysis validation."""
    return HTMLResponse(_dashboard_html())


@router.post("/validate/retrieval", response_model=RetrievalValidationResponse)
async def validate_retrieval(request: RetrievalValidationRequest):
    """Run representative or user-supplied retrieval checks."""
    cases = request.cases or _default_retrieval_cases()
    results: list[RetrievalValidationCaseResult] = []

    for case in cases:
        resolved_top_k = case.top_k if case.top_k is not None else request.top_k
        resolved_min_similarity = (
            case.min_similarity
            if case.min_similarity is not None
            else request.min_similarity
        )
        query = f"{case.event_type} {case.sensor_name} {case.vessel_id}"
        docs = await retrieve_context_for_query(
            query,
            top_k=resolved_top_k,
            min_similarity=resolved_min_similarity,
        )
        results.append(
            RetrievalValidationCaseResult(
                name=case.name,
                query=query,
                expected_sources=case.expected_sources,
                matched_expected_source=_matched_expected_source(
                    docs,
                    case.expected_sources,
                ),
                retrieved_documents=[_serialize_doc(doc) for doc in docs],
            )
        )

    matched_cases = sum(1 for result in results if result.matched_expected_source)
    return RetrievalValidationResponse(
        total_cases=len(results),
        matched_cases=matched_cases,
        requested_top_k=request.top_k,
        requested_min_similarity=request.min_similarity,
        results=results,
    )


@router.post("/validate/analysis", response_model=AnalysisValidationResponse)
async def validate_analysis(request: AnalysisValidationRequest):
    """
    Run one event through the quick analysis pipeline without saving a new row.
    Returns retrieval diagnostics and tool-call traces that affect output quality.
    """
    pool = get_pool()
    async with pool.acquire() as conn:
        event = await conn.fetchrow(
            "SELECT * FROM events WHERE id = $1",
            request.event_id,
        )
    if event is None:
        raise HTTPException(status_code=404, detail=f"Event {request.event_id} not found")

    event_dict = dict(event)
    result = await run_quick_analysis_pipeline(
        event_dict,
        rag_top_k=request.top_k,
        rag_min_similarity=request.min_similarity,
        model_name=VALIDATION_MODEL or None,
    )

    resolved_top_k = request.top_k if request.top_k is not None else QUICK_ANALYSIS_TOP_K
    resolved_min_similarity = (
        request.min_similarity
        if request.min_similarity is not None
        else RAG_MIN_SIMILARITY
    )

    return AnalysisValidationResponse(
        event=EventSchema(**event_dict),
        analysis_text=result.analysis_text,
        suggested_actions=result.suggested_actions,
        confidence=result.confidence,
        retrieved_documents=[_serialize_doc(doc) for doc in result.context_docs],
        tool_calls=[
            ToolCallTrace(
                name=tool.name,
                arguments=tool.arguments,
                succeeded=tool.succeeded,
                response_size_chars=tool.response_size_chars,
                response_preview=tool.response_preview,
            )
            for tool in result.tool_calls
        ],
        quality_factors=AnalysisQualityFactors(
            rag_top_k=resolved_top_k,
            rag_min_similarity=resolved_min_similarity,
            retrieved_documents_count=len(result.context_docs),
            retrieved_sources=[doc.source for doc in result.context_docs],
            tool_calls_count=len(result.tool_calls),
            used_live_tools=any(tool.succeeded for tool in result.tool_calls),
            model_used=result.model_used,
            status=result.status,
        ),
    )


def _serialize_doc(doc) -> RetrievedDocument:
    return RetrievedDocument(
        title=doc.title,
        source=doc.source,
        similarity=doc.similarity,
        content_preview=_preview_content(doc.content),
    )


def _preview_content(content: str, max_chars: int = 240) -> str:
    compact = " ".join(content.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3] + "..."


def _matched_expected_source(docs: list, expected_sources: list[str]) -> bool:
    if not expected_sources:
        return False

    normalized_expected = [value.lower() for value in expected_sources]
    for doc in docs:
        source = doc.source.lower()
        if any(source.endswith(expected) for expected in normalized_expected):
            return True
    return False


def _default_retrieval_cases() -> list[RetrievalValidationCase]:
    """Representative event types called out in the project backlog."""
    return [
        RetrievalValidationCase(
            name="charge_air_temp",
            event_type="HIGH_DG5_CHARGE_AIR_TEMP",
            sensor_name="dg5_charge_air_temp",
            expected_sources=["main_engine.md", "p3_normal_values_thresholds.md"],
        ),
        RetrievalValidationCase(
            name="fuel_viscosity",
            event_type="HIGH_HFO_FUEL_VISCOSITY",
            sensor_name="hfo_fuel_viscosity",
            expected_sources=["fuel_system.md", "p3_normal_values_thresholds.md"],
        ),
        RetrievalValidationCase(
            name="scrubber_so2",
            event_type="HIGH_SCRUBBER_FWD_SO2",
            sensor_name="scrubber_fwd_so2",
            expected_sources=[
                "fuel_system.md",
                "p3_normal_values_thresholds.md",
                "p9_maritime_regulations.md",
            ],
        ),
        RetrievalValidationCase(
            name="low_lo_flow",
            event_type="LOW_CLEAN_LO_FLOW",
            sensor_name="clean_lo_flow",
            expected_sources=["main_engine.md", "p5_troubleshooting_procedures.md"],
        ),
        RetrievalValidationCase(
            name="engine_overload",
            event_type="HIGH_DG3_ENGINE_LOAD",
            sensor_name="dg3_engine_load",
            expected_sources=["auxiliary_engines.md", "main_engine.md"],
        ),
        RetrievalValidationCase(
            name="low_tank_weight",
            event_type="LOW_HFO_TANK_WEIGHT",
            sensor_name="hfo_tank_weight",
            expected_sources=["fuel_system.md", "p3_normal_values_thresholds.md"],
        ),
    ]


def _dashboard_html() -> str:
    return """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Validation Dashboard</title>
  <style>
    :root {
      --bg: #f5f1e8;
      --panel: rgba(255, 252, 245, 0.88);
      --ink: #10233a;
      --muted: #5f6f7d;
      --line: rgba(16, 35, 58, 0.14);
      --accent: #c26b2f;
      --accent-strong: #8d3f18;
      --good: #1f7a4c;
      --warn: #b7791f;
      --bad: #b33a3a;
      --shadow: 0 16px 38px rgba(16, 35, 58, 0.08);
    }

    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: "Segoe UI", "Helvetica Neue", sans-serif;
      color: var(--ink);
      background:
        radial-gradient(circle at top left, rgba(194, 107, 47, 0.16), transparent 28%),
        radial-gradient(circle at top right, rgba(16, 35, 58, 0.10), transparent 30%),
        linear-gradient(180deg, #f8f3ea 0%, #efe7da 100%);
      min-height: 100vh;
    }

    .shell {
      max-width: 1240px;
      margin: 0 auto;
      padding: 32px 20px 64px;
    }

    .hero {
      display: grid;
      gap: 14px;
      margin-bottom: 24px;
    }

    .eyebrow {
      font-size: 12px;
      letter-spacing: 0.18em;
      text-transform: uppercase;
      color: var(--accent-strong);
      font-weight: 700;
    }

    h1 {
      margin: 0;
      font-size: clamp(28px, 4vw, 48px);
      line-height: 0.95;
      max-width: 10ch;
    }

    .hero p {
      margin: 0;
      max-width: 68ch;
      color: var(--muted);
      line-height: 1.6;
    }

    .grid {
      display: grid;
      grid-template-columns: repeat(12, minmax(0, 1fr));
      gap: 18px;
    }

    .panel {
      grid-column: span 12;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 24px;
      box-shadow: var(--shadow);
      padding: 22px;
      backdrop-filter: blur(10px);
    }

    .panel h2 {
      margin: 0 0 6px;
      font-size: 20px;
    }

    .panel p {
      margin: 0 0 18px;
      color: var(--muted);
      line-height: 1.5;
    }

    .controls {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 16px;
    }

    label {
      display: grid;
      gap: 6px;
      font-size: 13px;
      color: var(--muted);
      font-weight: 600;
    }

    input {
      width: 100%;
      border: 1px solid var(--line);
      border-radius: 14px;
      padding: 11px 12px;
      font-size: 14px;
      background: rgba(255, 255, 255, 0.8);
      color: var(--ink);
    }

    .actions {
      display: flex;
      flex-wrap: wrap;
      gap: 10px;
      margin-bottom: 18px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 11px 16px;
      font-size: 14px;
      font-weight: 700;
      cursor: pointer;
      transition: transform 0.15s ease, box-shadow 0.15s ease;
      box-shadow: 0 10px 18px rgba(194, 107, 47, 0.14);
    }

    button:hover {
      transform: translateY(-1px);
    }

    .primary {
      background: linear-gradient(135deg, #c26b2f, #8d3f18);
      color: #fff9f3;
    }

    .secondary {
      background: rgba(16, 35, 58, 0.08);
      color: var(--ink);
      box-shadow: none;
    }

    .cards {
      display: grid;
      grid-template-columns: repeat(4, minmax(0, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }

    .card {
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      background: rgba(255, 255, 255, 0.7);
    }

    .metric {
      font-size: 28px;
      font-weight: 800;
      line-height: 1;
      margin-bottom: 6px;
    }

    .label {
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      color: var(--muted);
    }

    .status {
      margin-bottom: 14px;
      font-size: 14px;
      color: var(--muted);
      min-height: 1.4em;
    }

    .status.good { color: var(--good); }
    .status.warn { color: var(--warn); }
    .status.bad { color: var(--bad); }

    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
    }

    th, td {
      text-align: left;
      padding: 10px 8px;
      border-bottom: 1px solid rgba(16, 35, 58, 0.08);
      vertical-align: top;
    }

    th {
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .mono {
      font-family: "Consolas", "SFMono-Regular", monospace;
      font-size: 12px;
    }

    .pill {
      display: inline-flex;
      align-items: center;
      padding: 5px 10px;
      border-radius: 999px;
      font-size: 12px;
      font-weight: 700;
    }

    .pill.good { background: rgba(31, 122, 76, 0.12); color: var(--good); }
    .pill.bad { background: rgba(179, 58, 58, 0.12); color: var(--bad); }

    .analysis {
      display: grid;
      grid-template-columns: 1.3fr 1fr;
      gap: 14px;
    }

    pre {
      margin: 0;
      white-space: pre-wrap;
      line-height: 1.55;
      font-size: 13px;
      color: var(--ink);
      background: rgba(255, 255, 255, 0.7);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 16px;
      min-height: 220px;
    }

    .stack {
      display: grid;
      gap: 12px;
    }

    .mini-table {
      max-height: 360px;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 18px;
      background: rgba(255, 255, 255, 0.68);
    }

    @media (max-width: 980px) {
      .controls, .cards, .analysis {
        grid-template-columns: 1fr 1fr;
      }
    }

    @media (max-width: 760px) {
      .controls, .cards, .analysis {
        grid-template-columns: 1fr;
      }
    }
  </style>
</head>
<body>
  <div class="shell">
    <section class="hero">
      <div class="eyebrow">Internal Validation</div>
      <h1>RAG and analysis quality bench</h1>
      <p>
        Use the same live agent pipeline to benchmark retrieval, compare top-K and similarity
        settings, and inspect which documents and tool calls shaped a single analysis run.
      </p>
    </section>

    <div class="grid">
      <section class="panel">
        <h2>Retrieval Benchmark</h2>
        <p>Runs the fixed benchmark suite through <span class="mono">/api/v1/validate/retrieval</span>.</p>
        <div class="controls">
          <label>Top-K
            <input id="retrievalTopK" type="number" min="1" max="20" placeholder="Use server default">
          </label>
          <label>Min similarity
            <input id="retrievalMinSim" type="number" min="0" max="1" step="0.01" placeholder="Use server default">
          </label>
          <label>Matched cases
            <input id="matchedCases" type="text" value="-" readonly>
          </label>
          <label>Top-hit matches
            <input id="topHitCases" type="text" value="-" readonly>
          </label>
        </div>
        <div class="actions">
          <button class="primary" id="runRetrieval">Run benchmark</button>
        </div>
        <div class="status" id="retrievalStatus"></div>
        <div class="cards">
          <div class="card">
            <div class="metric" id="retrievalCardMatched">-</div>
            <div class="label">Cases matched</div>
          </div>
          <div class="card">
            <div class="metric" id="retrievalCardExpectedHits">-</div>
            <div class="label">Expected hits</div>
          </div>
          <div class="card">
            <div class="metric" id="retrievalCardSources">-</div>
            <div class="label">Average unique sources</div>
          </div>
          <div class="card">
            <div class="metric" id="retrievalCardDocs">-</div>
            <div class="label">Average docs returned</div>
          </div>
        </div>
        <div class="mini-table">
          <table id="retrievalTable">
            <thead>
              <tr>
                <th>Case</th>
                <th>Match</th>
                <th>Top hit</th>
                <th>Top similarity</th>
                <th>Sources</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </section>

      <section class="panel">
        <h2>Analysis Validation</h2>
        <p>
          Run a fast validation pass through <span class="mono">/api/v1/validate/analysis</span>
          without writing a new row, or start a persisted full analysis job through
          <span class="mono">/api/v1/analyze/full</span>.
        </p>
        <div class="controls">
          <label>Event ID
            <input id="analysisEventId" type="number" min="1" placeholder="Fetch latest event or enter one">
          </label>
          <label>Top-K override
            <input id="analysisTopK" type="number" min="1" max="20" placeholder="Use server default">
          </label>
          <label>Min similarity override
            <input id="analysisMinSim" type="number" min="0" max="1" step="0.01" placeholder="Use server default">
          </label>
          <label>Pipeline status
            <input id="analysisPipelineStatus" type="text" value="-" readonly>
          </label>
          <label>Elapsed time
            <input id="analysisElapsed" type="text" value="-" readonly>
          </label>
        </div>
        <div class="actions">
          <button class="secondary" id="useLatestEvent">Use latest event</button>
          <button class="secondary" id="runQuickAnalysis">Run quick validation</button>
          <button class="primary" id="startFullAnalysis">Start full analysis</button>
        </div>
        <div class="status" id="analysisStatus"></div>
        <div class="cards">
          <div class="card">
            <div class="metric" id="analysisCardDocs">-</div>
            <div class="label">Retrieved docs</div>
          </div>
          <div class="card">
            <div class="metric" id="analysisCardTools">-</div>
            <div class="label">Tool calls</div>
          </div>
          <div class="card">
            <div class="metric" id="analysisCardConfidence">-</div>
            <div class="label">Confidence</div>
          </div>
          <div class="card">
            <div class="metric" id="analysisCardModel">-</div>
            <div class="label">Model</div>
          </div>
        </div>
        <div class="analysis">
          <pre id="analysisText">No analysis run yet.</pre>
          <div class="stack">
            <div class="mini-table">
              <table id="analysisDocsTable">
                <thead>
                  <tr>
                    <th>Source</th>
                    <th>Similarity</th>
                    <th>Preview</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
            <div class="mini-table">
              <table id="toolCallsTable">
                <thead>
                  <tr>
                    <th>Tool</th>
                    <th>OK</th>
                    <th>Args</th>
                    <th>Preview</th>
                  </tr>
                </thead>
                <tbody></tbody>
              </table>
            </div>
          </div>
        </div>
      </section>
    </div>
  </div>

  <script>
    let analysisTimerId = null;
    let fullAnalysisPollId = null;

    function parseOptionalNumber(value) {
      if (value === "" || value === null || value === undefined) {
        return null;
      }
      const parsed = Number(value);
      return Number.isFinite(parsed) ? parsed : null;
    }

    function formatElapsed(ms) {
      const totalSeconds = Math.max(Math.floor(ms / 1000), 0);
      const minutes = Math.floor(totalSeconds / 60);
      const seconds = totalSeconds % 60;
      if (minutes >= 60) {
        const hours = Math.floor(minutes / 60);
        const remainingMinutes = minutes % 60;
        return `${hours}h ${remainingMinutes}m ${seconds}s`;
      }
      if (minutes > 0) {
        return `${minutes}m ${seconds}s`;
      }
      return `${seconds}s`;
    }

    function setAnalysisElapsed(value) {
      document.getElementById("analysisElapsed").value = value;
    }

    function startAnalysisTimer() {
      if (analysisTimerId !== null) {
        clearInterval(analysisTimerId);
      }
      const startedAt = Date.now();
      setAnalysisElapsed("0s");
      analysisTimerId = setInterval(() => {
        setAnalysisElapsed(formatElapsed(Date.now() - startedAt));
      }, 1000);
      return startedAt;
    }

    function stopAnalysisTimer(startedAt) {
      if (analysisTimerId !== null) {
        clearInterval(analysisTimerId);
        analysisTimerId = null;
      }
      if (!startedAt) {
        return document.getElementById("analysisElapsed").value;
      }
      const elapsed = formatElapsed(Date.now() - startedAt);
      setAnalysisElapsed(elapsed);
      return elapsed;
    }

    function setStatus(element, text, tone = "") {
      element.textContent = text;
      element.className = tone ? `status ${tone}` : "status";
    }

    function average(values) {
      if (!values.length) {
        return 0;
      }
      return values.reduce((sum, value) => sum + value, 0) / values.length;
    }

    function normalizeExpected(result) {
      return result.expected_sources.map((value) => value.toLowerCase());
    }

    function isExpectedSource(source, expectedSources) {
      const normalized = source.toLowerCase();
      return expectedSources.some((expected) => normalized.endsWith(expected));
    }

    async function postJson(url, body) {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body)
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
      }
      return await response.json();
    }

    async function getJson(url) {
      const response = await fetch(url);
      if (!response.ok) {
        const text = await response.text();
        throw new Error(text || `HTTP ${response.status}`);
      }
      return await response.json();
    }

    async function loadLatestEvent() {
      const response = await fetch("/api/v1/events?limit=1");
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const payload = await response.json();
      if (Array.isArray(payload)) {
        if (!payload.length) {
          throw new Error("No events available.");
        }
        return payload[0];
      }
      if (payload && typeof payload === "object") {
        return payload;
      }
      throw new Error("Unexpected events response.");
    }

    function renderRetrieval(data) {
      const tbody = document.querySelector("#retrievalTable tbody");
      tbody.innerHTML = "";

      const topHitCases = data.results.filter((result) => {
        const topDoc = result.retrieved_documents[0];
        if (!topDoc) {
          return false;
        }
        return isExpectedSource(topDoc.source, normalizeExpected(result));
      }).length;

      const expectedHits = data.results.reduce((count, result) => {
        const expected = normalizeExpected(result);
        return count + result.retrieved_documents.filter((doc) => isExpectedSource(doc.source, expected)).length;
      }, 0);

      const avgUniqueSources = average(data.results.map((result) => {
        return new Set(result.retrieved_documents.map((doc) => doc.source)).size;
      }));
      const avgDocs = average(data.results.map((result) => result.retrieved_documents.length));

      document.getElementById("matchedCases").value = `${data.matched_cases}/${data.total_cases}`;
      document.getElementById("topHitCases").value = `${topHitCases}/${data.total_cases}`;
      document.getElementById("retrievalCardMatched").textContent = `${data.matched_cases}/${data.total_cases}`;
      document.getElementById("retrievalCardExpectedHits").textContent = String(expectedHits);
      document.getElementById("retrievalCardSources").textContent = avgUniqueSources.toFixed(2);
      document.getElementById("retrievalCardDocs").textContent = avgDocs.toFixed(2);

      for (const result of data.results) {
        const row = document.createElement("tr");
        const topDoc = result.retrieved_documents[0];
        const sources = [...new Set(result.retrieved_documents.map((doc) => doc.source))].join(", ");
        row.innerHTML = `
          <td class="mono">${result.name}</td>
          <td><span class="pill ${result.matched_expected_source ? "good" : "bad"}">${result.matched_expected_source ? "yes" : "no"}</span></td>
          <td class="mono">${topDoc ? topDoc.source : "-"}</td>
          <td>${topDoc ? topDoc.similarity.toFixed(3) : "-"}</td>
          <td class="mono">${sources || "-"}</td>
        `;
        tbody.appendChild(row);
      }
    }

    function renderAnalysis(data) {
      document.getElementById("analysisPipelineStatus").value = data.quality_factors.status;
      document.getElementById("analysisCardDocs").textContent = String(data.quality_factors.retrieved_documents_count);
      document.getElementById("analysisCardTools").textContent = String(data.quality_factors.tool_calls_count);
      document.getElementById("analysisCardConfidence").textContent = `${Math.round((data.confidence || 0) * 100)}%`;
      document.getElementById("analysisCardModel").textContent = data.quality_factors.model_used || "-";
      document.getElementById("analysisText").textContent = data.analysis_text || "No analysis text returned.";

      const docsTbody = document.querySelector("#analysisDocsTable tbody");
      docsTbody.innerHTML = "";
      for (const doc of data.retrieved_documents) {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td class="mono">${doc.source}</td>
          <td>${doc.similarity.toFixed(3)}</td>
          <td>${doc.content_preview}</td>
        `;
        docsTbody.appendChild(row);
      }

      const toolsTbody = document.querySelector("#toolCallsTable tbody");
      toolsTbody.innerHTML = "";
      for (const tool of data.tool_calls) {
        const row = document.createElement("tr");
        row.innerHTML = `
          <td class="mono">${tool.name}</td>
          <td><span class="pill ${tool.succeeded ? "good" : "bad"}">${tool.succeeded ? "yes" : "no"}</span></td>
          <td class="mono">${JSON.stringify(tool.arguments)}</td>
          <td>${tool.response_preview}</td>
        `;
        toolsTbody.appendChild(row);
      }
    }

    function clearAnalysisTables() {
      document.querySelector("#analysisDocsTable tbody").innerHTML = "";
      document.querySelector("#toolCallsTable tbody").innerHTML = "";
    }

    function renderFullAnalysis(data) {
      document.getElementById("analysisPipelineStatus").value = data.status;
      document.getElementById("analysisCardDocs").textContent = "n/a";
      document.getElementById("analysisCardTools").textContent = "n/a";
      document.getElementById("analysisCardConfidence").textContent = `${Math.round((data.confidence || 0) * 100)}%`;
      document.getElementById("analysisCardModel").textContent = data.model_used || "-";
      document.getElementById("analysisText").textContent =
        data.analysis_text || "Full analysis job is queued or running.";
      clearAnalysisTables();
    }

    function stopFullAnalysisPolling() {
      if (fullAnalysisPollId !== null) {
        clearInterval(fullAnalysisPollId);
        fullAnalysisPollId = null;
      }
    }

    document.getElementById("runRetrieval").addEventListener("click", async () => {
      const statusEl = document.getElementById("retrievalStatus");
      try {
        setStatus(statusEl, "Running retrieval benchmark...", "warn");
        const topK = parseOptionalNumber(document.getElementById("retrievalTopK").value);
        const minSimilarity = parseOptionalNumber(document.getElementById("retrievalMinSim").value);
        const payload = {};
        if (topK !== null) payload.top_k = topK;
        if (minSimilarity !== null) payload.min_similarity = minSimilarity;
        const data = await postJson("/api/v1/validate/retrieval", payload);
        renderRetrieval(data);
        setStatus(statusEl, `Completed benchmark: ${data.matched_cases}/${data.total_cases} cases matched.`, "good");
      } catch (error) {
        setStatus(statusEl, `Benchmark failed: ${error.message}`, "bad");
      }
    });

    document.getElementById("useLatestEvent").addEventListener("click", async () => {
      const statusEl = document.getElementById("analysisStatus");
      try {
        setStatus(statusEl, "Fetching latest event...", "warn");
        const latest = await loadLatestEvent();
        document.getElementById("analysisEventId").value = latest.id;
        setStatus(statusEl, `Loaded latest event ${latest.id} (${latest.event_type}).`, "good");
      } catch (error) {
        setStatus(statusEl, `Could not fetch latest event: ${error.message}`, "bad");
      }
    });

    document.getElementById("runQuickAnalysis").addEventListener("click", async () => {
      const statusEl = document.getElementById("analysisStatus");
      let startedAt = null;
      try {
        const eventId = parseOptionalNumber(document.getElementById("analysisEventId").value);
        if (eventId === null) {
          throw new Error("Enter an event id or use the latest event button first.");
        }
        stopFullAnalysisPolling();
        startedAt = startAnalysisTimer();
        setStatus(statusEl, `Running quick validation for event ${eventId}...`, "warn");
        const topK = parseOptionalNumber(document.getElementById("analysisTopK").value);
        const minSimilarity = parseOptionalNumber(document.getElementById("analysisMinSim").value);
        const payload = { event_id: eventId };
        if (topK !== null) payload.top_k = topK;
        if (minSimilarity !== null) payload.min_similarity = minSimilarity;
        const data = await postJson("/api/v1/validate/analysis", payload);
        renderAnalysis(data);
        const tone = data.quality_factors.status === "completed" ? "good" : "bad";
        const elapsed = stopAnalysisTimer(startedAt);
        setStatus(
          statusEl,
          `Quick validation finished with status ${data.quality_factors.status} in ${elapsed}.`,
          tone
        );
      } catch (error) {
        const elapsed = stopAnalysisTimer(startedAt);
        const suffix = startedAt ? ` after ${elapsed}` : "";
        setStatus(statusEl, `Quick validation failed${suffix}: ${error.message}`, "bad");
      }
    });

    document.getElementById("startFullAnalysis").addEventListener("click", async () => {
      const statusEl = document.getElementById("analysisStatus");
      let startedAt = null;
      try {
        const eventId = parseOptionalNumber(document.getElementById("analysisEventId").value);
        if (eventId === null) {
          throw new Error("Enter an event id or use the latest event button first.");
        }
        stopFullAnalysisPolling();
        startedAt = startAnalysisTimer();
        setStatus(statusEl, `Queueing full analysis for event ${eventId}...`, "warn");
        const topK = parseOptionalNumber(document.getElementById("analysisTopK").value);
        const minSimilarity = parseOptionalNumber(document.getElementById("analysisMinSim").value);
        const payload = { event_id: eventId };
        if (topK !== null) payload.top_k = topK;
        if (minSimilarity !== null) payload.min_similarity = minSimilarity;
        const job = await postJson("/api/v1/analyze/full", payload);
        renderFullAnalysis(job);
        setStatus(statusEl, `Full analysis job ${job.id} is ${job.status}.`, "warn");

        fullAnalysisPollId = setInterval(async () => {
          try {
            const current = await getJson(`/api/v1/analyses/${job.id}`);
            renderFullAnalysis(current);
            const elapsed = formatElapsed(Date.now() - startedAt);
            if (current.status === "completed" || current.status === "failed") {
              stopFullAnalysisPolling();
              stopAnalysisTimer(startedAt);
              const tone = current.status === "completed" ? "good" : "bad";
              setStatus(
                statusEl,
                `Full analysis finished with status ${current.status} in ${elapsed}.`,
                tone
              );
              return;
            }
            setStatus(
              statusEl,
              `Full analysis job ${job.id} is ${current.status}. Elapsed ${elapsed}.`,
              "warn"
            );
          } catch (error) {
            stopFullAnalysisPolling();
            const elapsed = stopAnalysisTimer(startedAt);
            setStatus(
              statusEl,
              `Full analysis polling failed after ${elapsed}: ${error.message}`,
              "bad"
            );
          }
        }, 3000);
      } catch (error) {
        stopFullAnalysisPolling();
        const elapsed = stopAnalysisTimer(startedAt);
        const suffix = startedAt ? ` after ${elapsed}` : "";
        setStatus(statusEl, `Full analysis failed${suffix}: ${error.message}`, "bad");
      }
    });

    document.getElementById("runRetrieval").click();
  </script>
</body>
</html>"""
