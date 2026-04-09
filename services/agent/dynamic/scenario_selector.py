"""Deterministic dynamic-dashboard scenario selection."""

from __future__ import annotations

from typing import Any


SCENARIO_METRICS: dict[str, list[str]] = {
    "service_down": [
        "process_cpu_usage",
        "http_error_rate_5xx",
        "process_uptime_seconds",
    ],
    "runtime_pressure": [
        "process_cpu_usage",
        "http_request_duration_p95",
        "http_error_rate_5xx",
        "db_query_duration_p95",
    ],
    "connectivity": [
        "last_sync_age_seconds",
        "process_cpu_usage",
    ],
    "generic_incident": [
        "http_error_rate_5xx",
        "process_cpu_usage",
        "http_request_duration_p95",
    ],
}


def metric_names_for_scenario(scenario_key: str) -> list[str]:
    return list(SCENARIO_METRICS.get(scenario_key, SCENARIO_METRICS["generic_incident"]))


def select_scenario(
    *,
    alert: dict[str, Any] | None = None,
    app_status: dict[str, Any] | None = None,
) -> str:
    """Map alert/status context into one deterministic scenario."""
    alert_name = str((alert or {}).get("alert_name") or "").strip().lower()
    alert_type = str((alert or {}).get("alert_type") or "").strip().lower()
    app_state = str((app_status or {}).get("status") or "").strip().lower()
    latest_metrics = list((app_status or {}).get("latest_metrics") or [])
    metric_values = {
        str(metric.get("metric_name") or "").strip().lower(): metric.get("value")
        for metric in latest_metrics
    }

    if _matches_service_down(alert_name, alert_type, app_state, metric_values):
        return "service_down"
    if _matches_connectivity(alert_name, alert_type, metric_values):
        return "connectivity"
    if _matches_runtime_pressure(alert_name, alert_type, metric_values):
        return "runtime_pressure"
    return "generic_incident"


def _matches_service_down(
    alert_name: str,
    alert_type: str,
    app_state: str,
    metric_values: dict[str, Any],
) -> bool:
    if any(token in alert_name for token in ("servicedown", "service down", "unavailable")):
        return True
    if alert_type in {"service_down", "app_down", "application_down"}:
        return True
    if app_state == "down":
        return True
    return _metric_number(metric_values.get("service_up")) <= 0 or _metric_number(
        metric_values.get("health_check_status")
    ) <= 0


def _matches_connectivity(
    alert_name: str,
    alert_type: str,
    metric_values: dict[str, Any],
) -> bool:
    if any(token in alert_name for token in ("reportingstale", "syncdelayed", "connectivity", "stale")):
        return True
    if alert_type in {"reporting_stale", "sync_delayed", "connectivity"}:
        return True
    if _metric_number(metric_values.get("reporting_stale")) >= 1:
        return True
    if _metric_number(metric_values.get("sync_delayed")) >= 1:
        return True
    return _metric_number(metric_values.get("last_sync_age_seconds")) >= 900


def _matches_runtime_pressure(
    alert_name: str,
    alert_type: str,
    metric_values: dict[str, Any],
) -> bool:
    if any(token in alert_name for token in ("resourcepressure", "highlatency", "latency", "pressure")):
        return True
    if alert_type in {"resource_pressure", "latency_degraded", "runtime_pressure"}:
        return True
    if _metric_number(metric_values.get("process_cpu_usage")) >= 80:
        return True
    if _metric_number(metric_values.get("http_request_duration_p95")) >= 1:
        return True
    if _metric_number(metric_values.get("http_error_rate_5xx")) >= 0.05:
        return True
    return _metric_number(metric_values.get("db_query_duration_p95")) >= 1


def _metric_number(value: Any) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0
