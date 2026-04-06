"""
User-facing AI chat routes.
"""

from dataclasses import dataclass
import json
import os
import re

import httpx
from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, field_validator

from llm.ollama_client import chat
from models import RetrievedDocument, ToolCallTrace
from rag.client import format_context_for_prompt, retrieve_context_for_query

MCP_URL = os.getenv("MCP_URL", "http://mcp:8001")
MCP_API_KEY = os.getenv("MCP_API_KEY", "").strip()
CHAT_MODEL = os.getenv("OLLAMA_CHAT_MODEL", "").strip()
FALLBACK_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
CHAT_TOP_K = max(int(os.getenv("CHAT_TOP_K", "4")), 1)
CHAT_MAX_TOOL_CALLS = max(int(os.getenv("CHAT_MAX_TOOL_CALLS", "2")), 1)
CHAT_NUM_PREDICT = max(int(os.getenv("CHAT_NUM_PREDICT", "320")), 128)
GRAFANA_PUBLIC_URL = os.getenv("GRAFANA_PUBLIC_URL", "http://localhost:3000").strip()

# Maximum chars of an MCP tool response that the chat tool loop is allowed to
# feed back into the model context. Mirrors analyze.py's MAX_TOOL_RESULT_CHARS
# so the chat path cannot blow past llama3.2's context window. The full payload
# is still kept in the trace for the UI.
MAX_CHAT_TOOL_RESULT_CHARS = 1500
# UDS-only allowlist. Kept in sync with analyze.py's UDS_FULL_TOOL_NAMES so the
# chat assistant exposes the same operational toolset and never picks the
# legacy telemetry/event tools by mistake.
CHAT_TOOL_NAMES = {
    "get_vessel_app_status",
    "get_vessel_alerts",
    "get_app_metric_history",
    "get_app_logs",
    "get_fleet_status",
    "get_fleet_alerts",
    "get_cross_vessel_correlation",
    "get_incident_timeline",
    "get_operational_snapshot",
}

router = APIRouter(tags=["chat"])

HOUR_WINDOW_TOOLS = {
    "get_vessel_alerts",
    "get_app_metric_history",
    "get_app_logs",
    "get_fleet_alerts",
    "get_cross_vessel_correlation",
    "get_incident_timeline",
}


@dataclass
class ChatPipelineResult:
    answer_text: str
    model_used: str
    status: str
    retrieved_documents: list[RetrievedDocument]
    tool_calls: list[ToolCallTrace]
    live_tools_attempted: bool = False
    live_tools_failed: bool = False


@dataclass
class DirectToolPlan:
    name: str
    arguments: dict


class ChatRequest(BaseModel):
    question: str = Field(min_length=3, max_length=600)

    @field_validator("question")
    @classmethod
    def _normalize_question(cls, value: str) -> str:
        # Collapse internal whitespace and reject input that is empty after
        # trimming. min_length=3 only checks the raw value, so "   " would
        # otherwise reach the pipeline as an empty question.
        normalized = " ".join((value or "").split()).strip()
        if len(normalized) < 3:
            raise ValueError("question must contain at least 3 non-whitespace characters")
        return normalized


class ChatResponse(BaseModel):
    question: str
    answer_text: str
    model_used: str
    status: str
    used_live_tools: bool
    live_tools_failed: bool = False
    retrieved_documents: list[RetrievedDocument] = Field(default_factory=list)
    tool_calls: list[ToolCallTrace] = Field(default_factory=list)


@router.get("/chat", response_class=HTMLResponse)
async def chat_page():
    """Browser-friendly chat page for the demo flow."""
    return HTMLResponse(_render_chat_html())


@router.post("/chat", response_model=ChatResponse)
async def submit_chat(request: ChatRequest):
    """Answer one operational question with MCP tools and optional RAG support."""
    question = request.question  # already normalized by the validator
    result = await run_chat_pipeline(question)
    return ChatResponse(
        question=question,
        answer_text=result.answer_text,
        model_used=result.model_used,
        status=result.status,
        used_live_tools=any(tool.succeeded for tool in result.tool_calls),
        live_tools_failed=result.live_tools_failed,
        retrieved_documents=result.retrieved_documents,
        tool_calls=result.tool_calls,
    )


async def run_chat_pipeline(question: str) -> ChatPipelineResult:
    """Run one free-form operational question through RAG + MCP-backed chat."""
    resolved_model = CHAT_MODEL or FALLBACK_MODEL
    docs = await retrieve_context_for_query(question, top_k=CHAT_TOP_K)
    prompt_context = format_context_for_prompt(docs)
    direct_plan = _plan_direct_tool_call(question)

    if direct_plan is not None:
        direct_result, succeeded = await _call_chat_tool(
            direct_plan.name,
            direct_plan.arguments,
        )
        tool_calls = [
            ToolCallTrace(
                name=direct_plan.name,
                arguments=direct_plan.arguments,
                succeeded=succeeded,
                response_size_chars=len(direct_result),
                response_preview=_preview_text(direct_result),
            )
        ]
        if succeeded:
            return ChatPipelineResult(
                answer_text=_summarize_direct_tool_result(
                    question,
                    direct_plan.name,
                    direct_result,
                ),
                model_used="direct-mcp-summary",
                status="completed",
                retrieved_documents=[_serialize_doc(doc) for doc in docs],
                tool_calls=tool_calls,
                live_tools_attempted=True,
                live_tools_failed=False,
            )
        # Direct shortcut failed -- fall through to the LLM tool loop so the
        # model can self-correct, but remember that we already attempted live
        # tools so the UI surfaces a warning if everything keeps failing.

    tools = await _fetch_chat_tools()
    tool_discovery_failed = not tools

    try:
        answer_text, tool_calls = await _run_chat_tool_loop(
            question,
            prompt_context,
            tools,
            model_name=resolved_model,
        )
        status = "completed"
    except Exception as exc:
        error_text = str(exc).strip() or exc.__class__.__name__
        answer_text = (
            "The assistant could not complete this request.\n\n"
            f"Error: {error_text}\n\n"
            "Check agent, MCP, and Ollama availability, then retry."
        )
        tool_calls = []
        status = "failed"

    live_tools_attempted = (
        bool(tool_calls)
        or direct_plan is not None
        or (not tool_discovery_failed)
    )
    live_tools_succeeded = any(t.succeeded for t in tool_calls)
    # Failure surface: tool discovery returned nothing, OR every tool call we
    # made errored out, OR the direct shortcut already failed and the LLM
    # loop never recovered with a successful call.
    live_tools_failed = (
        tool_discovery_failed
        or (bool(tool_calls) and not live_tools_succeeded)
        or (direct_plan is not None and not live_tools_succeeded)
    )

    if live_tools_failed and status == "completed":
        warning = (
            "[Warning] Live data was unavailable for this question -- the answer "
            "below is not grounded in current MCP tool output. Verify against the "
            "dashboards before acting on it.\n\n"
        )
        answer_text = warning + answer_text

    return ChatPipelineResult(
        answer_text=answer_text,
        model_used=resolved_model,
        status=status,
        retrieved_documents=[_serialize_doc(doc) for doc in docs],
        tool_calls=tool_calls,
        live_tools_attempted=live_tools_attempted,
        live_tools_failed=live_tools_failed,
    )


async def _run_chat_tool_loop(
    question: str,
    context: str,
    tools: list[dict],
    model_name: str,
) -> tuple[str, list[ToolCallTrace]]:
    messages: list[dict] = [
        {"role": "system", "content": _chat_system_prompt(context)},
        {"role": "user", "content": question},
    ]
    tool_traces: list[ToolCallTrace] = []
    pseudo_tool_retries = 0

    for _ in range(CHAT_MAX_TOOL_CALLS + 1):
        response = await chat(
            messages,
            tools=tools or None,
            model=model_name,
            options={
                "temperature": 0.1,
                "num_predict": CHAT_NUM_PREDICT,
                # Match analyze.py: enlarged context window so cold-cache
                # tool-call rounds (incident timeline, operational snapshot)
                # do not silently truncate the prompt.
                "num_ctx": 8192,
            },
        )
        tool_calls = response.get("tool_calls")
        content = (response.get("content") or "").strip()

        if not tool_calls:
            if _looks_like_pseudo_tool_call(content):
                pseudo_tool_retries += 1
                if pseudo_tool_retries <= 2:
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "Do not print pseudo tool calls or raw JSON. "
                                "Use the tool-calling interface directly if you need live data, "
                                "otherwise answer the question plainly."
                            ),
                        }
                    )
                    continue
                return await _run_single_pass_chat(question, context, model_name), tool_traces

            return content or "No answer generated.", tool_traces

        messages.append(
            {
                "role": "assistant",
                "content": content,
                "tool_calls": tool_calls,
            }
        )

        for tool_call in tool_calls:
            fn = tool_call.get("function", {})
            name = fn.get("name", "")
            args = fn.get("arguments", {})
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except json.JSONDecodeError:
                    args = {}
            if not isinstance(args, dict):
                args = {}
            args = _normalize_tool_arguments(name, args, question)

            result, succeeded = await _call_chat_tool(name, args)
            tool_traces.append(
                ToolCallTrace(
                    name=name,
                    arguments=args,
                    succeeded=succeeded,
                    response_size_chars=len(result),
                    response_preview=_preview_text(result),
                )
            )
            # Truncate large MCP payloads before feeding them back to the
            # model so the prompt does not blow past the context window.
            # The trace above keeps the full size for the UI.
            llm_result = result
            if len(result) > MAX_CHAT_TOOL_RESULT_CHARS:
                llm_result = result[:MAX_CHAT_TOOL_RESULT_CHARS] + "\n... [truncated]"
            messages.append({"role": "tool", "name": name, "content": llm_result})
            if not succeeded:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "The last tool call failed. Read the tool error, correct the arguments, "
                            "and try again if live data is still needed. Do not answer from memory."
                        ),
                    }
                )

    fallback = await _run_single_pass_chat(question, context, model_name)
    return fallback, tool_traces


async def _run_single_pass_chat(question: str, context: str, model_name: str) -> str:
    """Fallback path when tool calling is unavailable or the model misbehaves."""
    response = await chat(
        [
            {"role": "system", "content": _chat_system_prompt(context)},
            {"role": "user", "content": question},
        ],
        model=model_name,
        options={
            "temperature": 0.1,
            "num_predict": CHAT_NUM_PREDICT,
            "num_ctx": 8192,
        },
    )
    return (response.get("content") or "").strip() or "No answer generated."


async def _fetch_chat_tools() -> list[dict]:
    """Fetch MCP tools and expose the stable 12-tool set to the chat page."""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(f"{MCP_URL}/tools", headers=_mcp_headers())
            resp.raise_for_status()
            mcp_tools = resp.json().get("tools", [])
    except Exception as exc:
        print(f"[agent] Could not fetch chat MCP tools: {exc}")
        return []

    filtered_tools = [
        tool for tool in mcp_tools if tool.get("name") in CHAT_TOOL_NAMES
    ]
    return [
        {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool["description"],
                "parameters": tool.get("inputSchema", {}),
            },
        }
        for tool in filtered_tools
    ]


async def _call_chat_tool(name: str, arguments: dict) -> tuple[str, bool]:
    """Execute one MCP tool call for the chat assistant."""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{MCP_URL}/tools/call",
                json={"name": name, "arguments": arguments},
                headers=_mcp_headers(),
            )
            resp.raise_for_status()
            return json.dumps(resp.json()), True
    except Exception as exc:
        return json.dumps({"error": str(exc)}), False


def _chat_system_prompt(context: str) -> str:
    rag_section = ""
    if context and "not yet implemented" not in context:
        rag_section = f"\nRelevant documentation:\n{context}\n"

    return (
        "You are a maritime observability assistant for vessel operations, incident handling, "
        "and NOC support.\n"
        "Answer the user's question directly and concisely.\n"
        "Use live MCP tools when the question depends on current or historical system data.\n"
        "If a tool call fails, correct the arguments and retry before answering.\n"
        "For questions like 'right now', 'currently', or 'at the moment', use the smallest valid "
        "time window accepted by the tool. Never use zero-hour windows.\n"
        "Use retrieved documentation only as supporting context, not as a substitute for live data.\n"
        "Never invent vessel names, alerts, app states, or metrics.\n"
        "Never mention tools or capabilities that are not present in the provided tool list.\n"
        "If data is missing or ambiguous, say so clearly.\n"
        "Do not output raw JSON, tool names, or code blocks unless the user explicitly asks for them.\n"
        "Keep the final answer short, practical, and demo-friendly."
        + rag_section
    )


def _plan_direct_tool_call(question: str) -> DirectToolPlan | None:
    """Route common demo questions to one reliable MCP call."""
    lower = (question or "").lower()
    hours = _extract_hours_from_question(question)
    # Only direct-route to the UDS-specific shortcuts when we have an IMO
    # number. Legacy IDs like vessel_001 must fall through to the LLM tool
    # loop, which can resolve them via the broader tool set instead of being
    # handed to UDS-only tools that expect IMO format.
    vessel_id = _extract_imo_vessel_id(question)

    if "which vessels" in lower and "alert" in lower:
        severity = None
        for candidate in ("critical", "warning", "info"):
            if candidate in lower:
                severity = candidate
                break
        return DirectToolPlan(
            name="get_fleet_alerts",
            arguments=_normalize_tool_arguments(
                "get_fleet_alerts",
                {"hours": hours, "severity": severity},
                question,
            ),
        )

    if vessel_id and ("what happened" in lower or "timeline" in lower or "last" in lower or "past" in lower):
        return DirectToolPlan(
            name="get_incident_timeline",
            arguments=_normalize_tool_arguments(
                "get_incident_timeline",
                {"vessel_id": vessel_id, "hours": hours},
                question,
            ),
        )

    # "Which app is degraded across multiple vessels?" is a headline demo
    # question. get_cross_vessel_correlation is the right MCP tool for it
    # (it groups apps by COUNT(DISTINCT vessel) > 1) -- the previous bug was
    # in the *summarizer*, which has now been rewritten to actually frame
    # the answer as "apps degraded across multiple vessels".
    if (
        "across multiple vessels" in lower
        or "multiple vessels" in lower
        or "cross-vessel" in lower
        or "cross vessel" in lower
    ):
        return DirectToolPlan(
            name="get_cross_vessel_correlation",
            arguments=_normalize_tool_arguments(
                "get_cross_vessel_correlation",
                {"hours": hours},
                question,
            ),
        )

    if vessel_id and ("snapshot" in lower or "full state" in lower or "operational state" in lower):
        return DirectToolPlan(
            name="get_operational_snapshot",
            arguments={"vessel_id": vessel_id},
        )

    return None


def _summarize_direct_tool_result(question: str, tool_name: str, result_text: str) -> str:
    """Return a fast grounded answer for the most common demo questions."""
    try:
        payload = json.loads(result_text)
    except json.JSONDecodeError:
        return "The live tool returned data, but the response could not be summarized cleanly."

    if tool_name == "get_fleet_alerts":
        return _summarize_fleet_alerts(payload)
    if tool_name == "get_cross_vessel_correlation":
        return _summarize_cross_vessel_correlation(payload)
    if tool_name == "get_incident_timeline":
        return _summarize_incident_timeline(payload)
    if tool_name == "get_operational_snapshot":
        return _summarize_operational_snapshot(payload)

    return f"Live data was retrieved for: {question}"


def _serialize_doc(doc) -> RetrievedDocument:
    return RetrievedDocument(
        title=doc.title,
        source=doc.source,
        similarity=float(doc.similarity or 0.0),
        content_preview=_preview_text(doc.content, max_chars=240),
    )


def _mcp_headers() -> dict[str, str]:
    if not MCP_API_KEY:
        return {}
    return {"X-API-Key": MCP_API_KEY}


def _preview_text(text: str, max_chars: int = 400) -> str:
    compact = " ".join((text or "").split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 3] + "..."


def _looks_like_pseudo_tool_call(text: str) -> bool:
    compact = " ".join((text or "").strip().split())
    if not compact:
        return False
    return (
        compact.startswith("{")
        and '"name"' in compact
        and ('"parameters"' in compact or '"arguments"' in compact or '"tool"' in compact)
    )


def _normalize_tool_arguments(name: str, arguments: dict, question: str) -> dict:
    """Repair common argument-shape mistakes before calling MCP."""
    normalized = dict(arguments)

    if name in HOUR_WINDOW_TOOLS:
        normalized["hours"] = _coerce_bounded_int(
            normalized.get("hours"),
            default=_default_hours_for_question(question),
            minimum=1,
            maximum=168,
        )

    if name == "get_telemetry":
        normalized["minutes_back"] = _coerce_bounded_int(
            normalized.get("minutes_back"),
            default=60,
            minimum=1,
            maximum=1440,
        )

    if "severity" in normalized and isinstance(normalized["severity"], str):
        normalized["severity"] = normalized["severity"].strip().lower() or None

    return normalized


def _default_hours_for_question(question: str) -> int:
    lower = (question or "").lower()
    if any(token in lower for token in ("right now", "currently", "at the moment", "current")):
        return 1
    if "last 6 hours" in lower or "past 6 hours" in lower:
        return 6
    if "last 12 hours" in lower or "past 12 hours" in lower:
        return 12
    if "last 48 hours" in lower or "past 48 hours" in lower:
        return 48
    return 24


def _extract_hours_from_question(question: str) -> int:
    match = re.search(r"(?:last|past)\s+(\d+)\s+hours?", question, re.IGNORECASE)
    if match:
        return _coerce_bounded_int(match.group(1), default=24, minimum=1, maximum=168)
    return _default_hours_for_question(question)


def _extract_vessel_id(question: str) -> str | None:
    """Best-effort extraction of any vessel-shaped identifier in the question.

    Accepts both IMO numbers and legacy ``vessel_NNN`` identifiers. Callers
    that need an IMO-only value (e.g. UDS direct shortcuts) should use
    :func:`_extract_imo_vessel_id` instead.
    """
    match = re.search(r"\b(IMO\d{7}|vessel_\d+)\b", question, re.IGNORECASE)
    if not match:
        return None
    return match.group(1).upper() if match.group(1).upper().startswith("IMO") else match.group(1)


def _extract_imo_vessel_id(question: str) -> str | None:
    """Return an IMO-format vessel id if present in the question, else None.

    Direct-tool shortcuts call UDS-only MCP tools, which expect IMO numbers.
    Legacy ``vessel_NNN`` identifiers must fall through to the LLM tool loop
    so the model can resolve them via the broader tool set, instead of being
    handed straight to a tool that will return 404.
    """
    match = re.search(r"\bIMO\d{7}\b", question, re.IGNORECASE)
    if not match:
        return None
    return match.group(0).upper()


def _coerce_bounded_int(value, default: int, minimum: int, maximum: int) -> int:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        resolved = default
    return max(minimum, min(resolved, maximum))


def _summarize_fleet_alerts(payload: dict) -> str:
    alerts = list(payload.get("alerts") or [])
    hours = payload.get("hours", 24)
    severity = payload.get("severity_filter") or "all"
    if not alerts:
        return f"No {severity} alerts were returned across the fleet in the last {hours} hour(s)."

    vessels: dict[str, list[str]] = {}
    for alert in alerts:
        vessel_label = f"{alert.get('vessel_name', 'Unknown vessel')} ({alert.get('imo_nr', '-')})"
        app_name = alert.get("app_name") or alert.get("app_external_id") or "Unknown app"
        vessels.setdefault(vessel_label, []).append(app_name)

    vessel_parts = []
    for vessel_label, apps in vessels.items():
        unique_apps = sorted(set(apps))
        vessel_parts.append(f"{vessel_label}: {', '.join(unique_apps[:4])}")

    return (
        f"There are {len(alerts)} {severity} alert(s) active in the last {hours} hour(s). "
        f"Affected vessel(s): {'; '.join(vessel_parts)}."
    )


def _summarize_cross_vessel_correlation(payload: dict) -> str:
    """Summarize cross-vessel correlation as 'apps degraded across multiple vessels'.

    The MCP tool already groups apps by COUNT(DISTINCT vessel) > 1, so every
    entry in ``correlated_apps`` is by definition an app with active alerts on
    at least two vessels. This summarizer frames the answer as a list of
    those apps, since "Which app is degraded across multiple vessels?" is one
    of the headline demo questions.
    """
    apps = list(payload.get("correlated_apps") or [])
    alert_types = list(payload.get("correlated_alert_types") or [])
    hours = payload.get("hours", 24)

    if not apps:
        if alert_types:
            top_alert = alert_types[0]
            return (
                f"No single application has active alerts on multiple vessels in the "
                f"last {hours} hour(s), but {top_alert.get('affected_vessels', 0)} "
                f"vessels share the alert pattern "
                f"'{top_alert.get('alert_name', top_alert.get('alert_type', 'unknown alert'))}'."
            )
        return (
            f"No application currently has active alerts spanning multiple vessels "
            f"in the last {hours} hour(s)."
        )

    # Build a compact, presenter-friendly list of degraded apps and the
    # vessels they are degraded on.
    app_lines: list[str] = []
    for entry in apps[:4]:
        name = entry.get("app_name") or entry.get("app_id") or "Unknown app"
        affected = entry.get("affected_vessels", 0)
        vessels = entry.get("vessels") or "vessels not listed"
        app_lines.append(f"{name} (degraded on {affected} vessels: {vessels})")

    if len(apps) == 1:
        header = (
            f"1 application is degraded across multiple vessels in the last "
            f"{hours} hour(s):"
        )
    else:
        header = (
            f"{len(apps)} applications are degraded across multiple vessels in the "
            f"last {hours} hour(s):"
        )

    return header + " " + "; ".join(app_lines) + "."


def _summarize_incident_timeline(payload: dict) -> str:
    vessel = payload.get("vessel") or {}
    timeline = list(payload.get("timeline") or [])
    hours = payload.get("hours", 24)
    vessel_label = f"{vessel.get('name', 'Unknown vessel')} ({vessel.get('imo_nr', '-')})"
    if not timeline:
        return f"No timeline entries were returned for {vessel_label} in the last {hours} hour(s)."

    recent = timeline[:5]
    recent_text = "; ".join(
        f"{entry.get('time', '-')}: {entry.get('application', 'Unknown app')} "
        f"{entry.get('event_type', 'event')} {entry.get('message', '')}".strip()
        for entry in recent
    )

    app_counts: dict[str, int] = {}
    for entry in timeline:
        app_name = entry.get("application") or "Unknown app"
        app_counts[app_name] = app_counts.get(app_name, 0) + 1
    top_apps = ", ".join(
        f"{name} ({count})"
        for name, count in sorted(app_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    )

    return (
        f"{vessel_label} has {len(timeline)} timeline entry/entries in the last {hours} hour(s). "
        f"Most active apps: {top_apps}. Most recent events: {recent_text}."
    )


def _summarize_operational_snapshot(payload: dict) -> str:
    """Summarize ``get_operational_snapshot`` output for the chat UI.

    Field names are aligned with the MCP handler in
    ``services/mcp/main.py::_run_get_operational_snapshot``:

    * Per-app entries use ``name`` and ``external_id`` (NOT ``app_name`` /
      ``app_external_id``); the latter shape is only used in the
      ``active_alerts`` list.
    * Status values are derived by ``_derive_app_status`` and may include
      ``healthy`` / ``degraded`` / ``critical`` / ``stale`` / ``down``.
    """
    vessel = payload.get("vessel") or {}
    apps = list(payload.get("applications") or [])
    alerts = list(payload.get("active_alerts") or [])
    vessel_label = f"{vessel.get('name', 'Unknown vessel')} ({vessel.get('imo_nr', '-')})"

    critical_apps: list[str] = []
    degraded_apps: list[str] = []
    down_apps: list[str] = []
    stale_apps: list[str] = []

    for app in apps:
        status = str(app.get("status") or "").lower()
        app_name = (
            app.get("name")
            or app.get("external_id")
            or app.get("app_name")
            or app.get("app_external_id")
            or "Unknown app"
        )
        if status in ("down", "offline"):
            down_apps.append(app_name)
        elif status == "critical":
            critical_apps.append(app_name)
        elif status == "stale":
            stale_apps.append(app_name)
        elif status == "degraded":
            degraded_apps.append(app_name)

    parts = [
        f"{vessel_label} snapshot: {len(alerts)} active alert(s) across {len(apps)} app(s).",
    ]
    if down_apps:
        parts.append(f"Down apps: {', '.join(down_apps[:4])}.")
    parts.append(
        f"Critical apps: {', '.join(critical_apps[:4]) if critical_apps else 'none'}."
    )
    parts.append(
        f"Degraded apps: {', '.join(degraded_apps[:4]) if degraded_apps else 'none'}."
    )
    if stale_apps:
        parts.append(f"Stale apps: {', '.join(stale_apps[:4])}.")
    return " ".join(parts)


def _render_chat_html() -> str:
    return _CHAT_HTML_TEMPLATE.replace("__GRAFANA_PUBLIC_URL__", GRAFANA_PUBLIC_URL)


_CHAT_HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>AI Operations Chat</title>
  <style>
    :root {
      --bg:#09111f;
      --panel:#101a2d;
      --panel-2:#15233d;
      --ink:#edf3ff;
      --muted:#97a8c5;
      --line:#253455;
      --accent:#2d7ff9;
      --accent-2:#2aa889;
      --danger:#d96a6a;
    }
    * { box-sizing:border-box; }
    body {
      margin:0;
      font-family:Segoe UI, Arial, sans-serif;
      background:
        radial-gradient(circle at top left, rgba(45,127,249,0.18), transparent 28%),
        radial-gradient(circle at top right, rgba(42,168,137,0.14), transparent 24%),
        linear-gradient(180deg, #09111f 0%, #0e1830 100%);
      color:var(--ink);
    }
    .wrap { max-width:1100px; margin:0 auto; padding:32px 18px 48px; }
    .hero {
      display:grid;
      gap:16px;
      grid-template-columns:1.2fr .8fr;
      margin-bottom:18px;
    }
    .card {
      background:rgba(16,26,45,0.95);
      border:1px solid var(--line);
      border-radius:18px;
      padding:18px;
      box-shadow:0 18px 40px rgba(0,0,0,0.18);
    }
    .eyebrow {
      color:#7db4ff;
      text-transform:uppercase;
      letter-spacing:.12em;
      font-size:12px;
      margin-bottom:10px;
    }
    h1 { margin:0 0 10px 0; font-size:34px; line-height:1.08; }
    p { margin:0; color:var(--muted); line-height:1.55; }
    .examples {
      display:grid;
      gap:10px;
      margin-top:14px;
    }
    .example-btn,
    button,
    .back-link {
      appearance:none;
      border:0;
      border-radius:12px;
      cursor:pointer;
      text-decoration:none;
      transition:transform .12s ease, opacity .12s ease, background .12s ease;
    }
    .example-btn {
      width:100%;
      padding:12px 14px;
      text-align:left;
      background:var(--panel-2);
      color:var(--ink);
      border:1px solid #30456f;
    }
    .example-btn:hover,
    button:hover,
    .back-link:hover { transform:translateY(-1px); }
    .composer {
      display:grid;
      gap:14px;
      margin-bottom:18px;
    }
    textarea {
      width:100%;
      min-height:120px;
      resize:vertical;
      border-radius:16px;
      border:1px solid var(--line);
      background:#0b1426;
      color:var(--ink);
      padding:16px;
      font:inherit;
      line-height:1.45;
    }
    textarea:focus { outline:2px solid rgba(45,127,249,0.55); outline-offset:2px; }
    .actions {
      display:flex;
      gap:12px;
      align-items:center;
      flex-wrap:wrap;
    }
    button {
      background:linear-gradient(135deg, var(--accent), #5ea0ff);
      color:white;
      padding:12px 16px;
      font-weight:600;
    }
    button[disabled] { opacity:.65; cursor:wait; }
    .back-link {
      display:inline-block;
      background:#203253;
      color:var(--ink);
      padding:12px 16px;
    }
    .status {
      min-height:20px;
      color:var(--muted);
      font-size:14px;
    }
    .status.error { color:var(--danger); }
    .status.ok { color:#7fd7bc; }
    .result-grid {
      display:grid;
      gap:18px;
      grid-template-columns:1.15fr .85fr;
    }
    .label {
      color:var(--muted);
      font-size:12px;
      text-transform:uppercase;
      letter-spacing:.08em;
      margin-bottom:8px;
    }
    .answer {
      white-space:pre-wrap;
      line-height:1.6;
      min-height:180px;
    }
    .meta {
      display:grid;
      grid-template-columns:repeat(2, minmax(0, 1fr));
      gap:12px;
      margin-bottom:16px;
    }
    .metric {
      background:#0b1426;
      border:1px solid var(--line);
      border-radius:14px;
      padding:12px;
    }
    details {
      background:#0b1426;
      border:1px solid var(--line);
      border-radius:14px;
      padding:12px 14px;
    }
    details + details { margin-top:12px; }
    summary {
      cursor:pointer;
      font-weight:600;
      color:var(--ink);
    }
    .trace-list,
    .doc-list {
      display:grid;
      gap:10px;
      margin-top:12px;
    }
    .trace-item,
    .doc-item {
      background:var(--panel);
      border:1px solid var(--line);
      border-radius:12px;
      padding:12px;
    }
    .mini {
      color:var(--muted);
      font-size:13px;
      line-height:1.45;
      white-space:pre-wrap;
      word-break:break-word;
    }
    .empty {
      color:var(--muted);
      font-style:italic;
    }
    @media (max-width: 880px) {
      .hero,
      .result-grid { grid-template-columns:1fr; }
      h1 { font-size:28px; }
    }
  </style>
</head>
<body>
  <div class="wrap">
    <section class="hero">
      <div class="card">
        <div class="eyebrow">Scope 3 / Task 2</div>
        <h1>AI Operations Chat</h1>
        <p>
          Ask operational questions about vessels, alerts, incidents, and app health.
          The assistant can use live MCP tools and relevant knowledge-base context before answering.
        </p>
      </div>
      <div class="card">
        <div class="label">Example Questions</div>
        <div class="examples">
          <button class="example-btn" type="button" data-question="Which vessels have critical alerts right now?">Which vessels have critical alerts right now?</button>
          <button class="example-btn" type="button" data-question="What happened on IMO9300001 in the last 6 hours?">What happened on IMO9300001 in the last 6 hours?</button>
          <button class="example-btn" type="button" data-question="Which app is degraded across multiple vessels?">Which app is degraded across multiple vessels?</button>
        </div>
      </div>
    </section>

    <section class="card composer">
      <label class="label" for="question">Question</label>
      <textarea id="question" name="question" placeholder="Ask about vessel status, alerts, degraded apps, recent incidents, or cross-vessel patterns."></textarea>
      <div class="actions">
        <button id="submitBtn" type="button">Ask Assistant</button>
        <a class="back-link" href="__GRAFANA_PUBLIC_URL__">Back to Grafana</a>
      </div>
      <div id="status" class="status">Ready.</div>
    </section>

    <section class="result-grid">
      <div class="card">
        <div class="label">Assistant Answer</div>
        <div id="answer" class="answer empty">Submit a question to see the answer here.</div>
      </div>
      <div class="card">
        <div class="label">Traceability</div>
        <div class="meta">
          <div class="metric">
            <div class="label">Status</div>
            <div id="traceStatus">Idle</div>
          </div>
          <div class="metric">
            <div class="label">Model / Live Tools</div>
            <div id="traceModel">-</div>
          </div>
        </div>
        <details open>
          <summary>Tool Call Trace</summary>
          <div id="toolTrace" class="trace-list">
            <div class="empty">No tool calls yet.</div>
          </div>
        </details>
        <details>
          <summary>Retrieved Documents</summary>
          <div id="docTrace" class="doc-list">
            <div class="empty">No documents retrieved yet.</div>
          </div>
        </details>
      </div>
    </section>
  </div>

  <script>
    const questionEl = document.getElementById("question");
    const submitBtn = document.getElementById("submitBtn");
    const statusEl = document.getElementById("status");
    const answerEl = document.getElementById("answer");
    const traceStatusEl = document.getElementById("traceStatus");
    const traceModelEl = document.getElementById("traceModel");
    const toolTraceEl = document.getElementById("toolTrace");
    const docTraceEl = document.getElementById("docTrace");

    function setExamples() {
      document.querySelectorAll(".example-btn").forEach((button) => {
        button.addEventListener("click", () => {
          questionEl.value = button.dataset.question || "";
          questionEl.focus();
        });
      });
    }

    function renderEmpty(container, message) {
      container.innerHTML = "";
      const el = document.createElement("div");
      el.className = "empty";
      el.textContent = message;
      container.appendChild(el);
    }

    function renderToolTrace(items) {
      if (!items || !items.length) {
        renderEmpty(toolTraceEl, "No live MCP tool calls were needed for this answer.");
        return;
      }
      toolTraceEl.innerHTML = "";
      items.forEach((item) => {
        const wrapper = document.createElement("div");
        wrapper.className = "trace-item";

        const title = document.createElement("div");
        title.textContent = item.name + (item.succeeded ? " (ok)" : " (failed)");
        title.style.fontWeight = "600";

        const meta = document.createElement("div");
        meta.className = "mini";
        meta.textContent =
          "args: " + JSON.stringify(item.arguments || {}) + "\\n" +
          "response preview: " + (item.response_preview || "");

        wrapper.appendChild(title);
        wrapper.appendChild(meta);
        toolTraceEl.appendChild(wrapper);
      });
    }

    function renderDocTrace(items) {
      if (!items || !items.length) {
        renderEmpty(docTraceEl, "No RAG documents were retrieved for this question.");
        return;
      }
      docTraceEl.innerHTML = "";
      items.forEach((item) => {
        const wrapper = document.createElement("div");
        wrapper.className = "doc-item";

        const title = document.createElement("div");
        title.textContent = item.title + " (" + item.source + ")";
        title.style.fontWeight = "600";

        const meta = document.createElement("div");
        meta.className = "mini";
        meta.textContent =
          "similarity: " + Number(item.similarity || 0).toFixed(3) + "\\n" +
          (item.content_preview || "");

        wrapper.appendChild(title);
        wrapper.appendChild(meta);
        docTraceEl.appendChild(wrapper);
      });
    }

    async function submitQuestion() {
      const question = questionEl.value.trim();
      if (!question) {
        statusEl.textContent = "Enter a question before submitting.";
        statusEl.className = "status error";
        questionEl.focus();
        return;
      }

      submitBtn.disabled = true;
      submitBtn.textContent = "Thinking...";
      statusEl.textContent = "Collecting live data and generating an answer...";
      statusEl.className = "status";
      answerEl.textContent = "Working...";
      answerEl.className = "answer";
      traceStatusEl.textContent = "Running";
      traceModelEl.textContent = "-";
      renderEmpty(toolTraceEl, "Waiting for tool trace...");
      renderEmpty(docTraceEl, "Waiting for retrieved documents...");

      try {
        const response = await fetch("/api/v1/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || "Request failed");
        }

        answerEl.textContent = data.answer_text || "No answer generated.";
        answerEl.className = "answer";
        traceStatusEl.textContent = data.status || "unknown";
        let liveToolsLabel;
        if (data.live_tools_failed) {
          liveToolsLabel = " / live tools failed (answer not grounded)";
        } else if (data.used_live_tools) {
          liveToolsLabel = " / live MCP tools used";
        } else {
          liveToolsLabel = " / no live tools used";
        }
        traceModelEl.textContent = (data.model_used || "-") + liveToolsLabel;
        renderToolTrace(data.tool_calls || []);
        renderDocTrace(data.retrieved_documents || []);
        statusEl.textContent = "Answer ready.";
        statusEl.className = "status ok";
      } catch (error) {
        answerEl.textContent = "The assistant could not complete the request.";
        answerEl.className = "answer";
        traceStatusEl.textContent = "failed";
        traceModelEl.textContent = "-";
        renderEmpty(toolTraceEl, "No trace available because the request failed.");
        renderEmpty(docTraceEl, "No retrieval trace available because the request failed.");
        statusEl.textContent = error.message || "Request failed";
        statusEl.className = "status error";
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = "Ask Assistant";
      }
    }

    submitBtn.addEventListener("click", submitQuestion);
    questionEl.addEventListener("keydown", (event) => {
      if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
        submitQuestion();
      }
    });

    setExamples();
  </script>
</body>
</html>"""
