"""Deterministic scenario classification based on alert_name / alert_type.

Maps an incoming alert to one of four scenario keys so the dashboard
builder can select the right panel set.
"""

SCENARIO_KEYWORDS: dict[str, list[str]] = {
    "service_down": [
        "down",
        "unavailable",
        "unreachable",
        "crash",
        "stopped",
        "offline",
        "not_running",
        "container_exit",
        "no_data",
        "stale",
    ],
    "runtime_pressure": [
        "memory",
        "cpu",
        "disk",
        "pressure",
        "oom",
        "swap",
        "throttle",
        "resource",
        "high_load",
        "heap",
        "queue",
        "backlog",
        "lag",
    ],
    "connectivity": [
        "timeout",
        "connect",
        "network",
        "dns",
        "latency",
        "packet_loss",
        "link",
        "satellite",
        "bandwidth",
        "unreachable",
        "refused",
    ],
}

SCENARIO_TITLES: dict[str, str] = {
    "service_down":       "Service Down",
    "runtime_pressure":   "Runtime Pressure",
    "connectivity":       "Connectivity Issue",
    "generic_incident":   "Incident",
}


def classify_scenario(alert_name: str, alert_type: str = "") -> str:
    """Return a scenario key for the given alert.

    Checks ``alert_name`` and ``alert_type`` (case-insensitive) against
    keyword lists in priority order. Falls back to ``"generic_incident"``.
    """
    haystack = (alert_name + " " + alert_type).lower()
    for scenario, keywords in SCENARIO_KEYWORDS.items():
        if any(kw in haystack for kw in keywords):
            return scenario
    return "generic_incident"
