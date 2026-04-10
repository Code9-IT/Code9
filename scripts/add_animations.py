"""One-time script to add animated banners and enhanced stat panels to static dashboards."""
import json
import os

BASE = os.path.join(os.path.dirname(__file__), "..", "grafana", "dashboards")

# ---------------------------------------------------------------------------
# Animated HTML banners
# ---------------------------------------------------------------------------

BANNER_UDS = (
    '<style>'
    '@keyframes live-blink{0%,100%{opacity:1}50%{opacity:0.2}}'
    '@keyframes gradient-sweep{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}'
    '@keyframes alert-ring{0%,100%{box-shadow:0 0 0 0 rgba(242,73,92,0.5)}70%{box-shadow:0 0 0 8px rgba(242,73,92,0)}}'
    '.live-bar{display:flex;align-items:center;padding:7px 18px;'
    'background:linear-gradient(270deg,#0d1117,#1a1d2e,#0d1b0d);'
    'background-size:400% 400%;animation:gradient-sweep 10s ease infinite;'
    'border-radius:6px;gap:14px;height:40px;border:1px solid #1e2d1e}'
    '.live-dot{width:9px;height:9px;border-radius:50%;background:#73BF69;'
    'box-shadow:0 0 7px #73BF69;animation:live-blink 1.2s step-start infinite;flex-shrink:0}'
    '.live-txt{font-size:11px;font-weight:700;letter-spacing:2px;color:#73BF69;text-transform:uppercase}'
    '.sep{color:#2a3a2a;font-size:16px}'
    '.sys-name{font-size:12px;color:#bbb;font-weight:500}'
    '.right-section{margin-left:auto;display:flex;align-items:center;gap:12px}'
    '.tag{font-size:10px;color:#444;letter-spacing:1px;text-transform:uppercase}'
    '</style>'
    '<div class="live-bar">'
    '<div class="live-dot"></div>'
    '<span class="live-txt">Live</span>'
    '<span class="sep">|</span>'
    '<span class="sys-name">UDS Incident Workbench &mdash; Real-time vessel application monitoring</span>'
    '<div class="right-section"><span class="tag">auto-refresh 30s</span></div>'
    '</div>'
)

BANNER_FLEET = (
    '<style>'
    '@keyframes live-blink{0%,100%{opacity:1}50%{opacity:0.2}}'
    '@keyframes gradient-sweep{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}'
    '@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(-3px)}}'
    '.live-bar{display:flex;align-items:center;padding:7px 18px;'
    'background:linear-gradient(270deg,#0d1117,#0d1a2e,#0d1117);'
    'background-size:400% 400%;animation:gradient-sweep 12s ease infinite;'
    'border-radius:6px;gap:14px;height:40px;border:1px solid #1a2030}'
    '.live-dot{width:9px;height:9px;border-radius:50%;background:#5794F2;'
    'box-shadow:0 0 7px #5794F2;animation:live-blink 1.4s step-start infinite;flex-shrink:0}'
    '.live-txt{font-size:11px;font-weight:700;letter-spacing:2px;color:#5794F2;text-transform:uppercase}'
    '.sep{color:#1e2535;font-size:16px}'
    '.sys-name{font-size:12px;color:#bbb;font-weight:500}'
    '.icon{font-size:17px;animation:bob 3.5s ease-in-out infinite}'
    '.right-section{margin-left:auto}'
    '.tag{font-size:10px;color:#444;letter-spacing:1px;text-transform:uppercase}'
    '</style>'
    '<div class="live-bar">'
    '<div class="live-dot"></div>'
    '<span class="live-txt">Live</span>'
    '<span class="sep">|</span>'
    '<span class="icon">&#128674;</span>'
    '<span class="sys-name">Fleet Overview &mdash; Multi-vessel operational status</span>'
    '<div class="right-section"><span class="tag">auto-refresh 30s</span></div>'
    '</div>'
)

BANNER_NOC = (
    '<style>'
    '@keyframes live-blink{0%,100%{opacity:1}50%{opacity:0.2}}'
    '@keyframes gradient-sweep{0%{background-position:0% 50%}50%{background-position:100% 50%}100%{background-position:0% 50%}}'
    '@keyframes noc-glow{0%,100%{border-color:#2a1800}50%{border-color:#FF780A66}}'
    '.live-bar{display:flex;align-items:center;padding:7px 18px;'
    'background:linear-gradient(270deg,#0d1117,#1a0e00,#0d1117);'
    'background-size:400% 400%;animation:gradient-sweep 8s ease infinite;'
    'border-radius:6px;gap:14px;height:40px;border:1px solid #2a1800;animation:gradient-sweep 8s ease infinite,noc-glow 2.5s ease-in-out infinite}'
    '.live-dot{width:9px;height:9px;border-radius:50%;background:#FF780A;'
    'box-shadow:0 0 7px #FF780A;animation:live-blink 1s step-start infinite;flex-shrink:0}'
    '.live-txt{font-size:11px;font-weight:700;letter-spacing:2px;color:#FF780A;text-transform:uppercase}'
    '.sep{color:#2a1800;font-size:16px}'
    '.sys-name{font-size:12px;color:#bbb;font-weight:500}'
    '.right-section{margin-left:auto}'
    '.tag{font-size:10px;color:#444;letter-spacing:1px;text-transform:uppercase}'
    '</style>'
    '<div class="live-bar">'
    '<div class="live-dot"></div>'
    '<span class="live-txt">Live</span>'
    '<span class="sep">|</span>'
    '<span class="sys-name">NOC Support Board &mdash; Network operations centre view</span>'
    '<div class="right-section"><span class="tag">auto-refresh 30s</span></div>'
    '</div>'
)


# ---------------------------------------------------------------------------
# Threshold helpers
# ---------------------------------------------------------------------------

def _thresholds(warn, crit):
    return {"mode": "absolute", "steps": [
        {"color": "green", "value": None},
        {"color": "yellow", "value": warn},
        {"color": "red", "value": crit},
    ]}


def _pick_thresholds(title: str) -> dict:
    t = title.lower()
    if "critical" in t:
        return _thresholds(1, 2)
    if "age" in t or "freshness" in t or "stale" in t:
        return {"mode": "absolute", "steps": [
            {"color": "green", "value": None},
            {"color": "yellow", "value": 300},
            {"color": "red", "value": 600},
        ]}
    if "alert" in t or "incident" in t or "affected" in t:
        return _thresholds(1, 5)
    return _thresholds(2, 6)


# ---------------------------------------------------------------------------
# Core upgrade function
# ---------------------------------------------------------------------------

def upgrade_dashboard(filename: str, banner_html: str, shift_y: int = 3) -> None:
    path = os.path.join(BASE, filename)
    with open(path) as f:
        dash = json.load(f)

    panels = dash.get("panels", [])

    # 1. Shift all panels down to make room for banner
    for p in panels:
        p["gridPos"]["y"] += shift_y
        for sub in p.get("panels", []):
            sub["gridPos"]["y"] += shift_y

    # 2. Enhance stat panels: background color, area sparkline, smart thresholds
    for p in panels:
        if p.get("type") != "stat":
            continue
        opts = p.setdefault("options", {})
        opts["colorMode"] = "background"
        if opts.get("graphMode") != "none":
            opts["graphMode"] = "area"
        fc = p.setdefault("fieldConfig", {})
        defaults = fc.setdefault("defaults", {})
        existing = (defaults.get("thresholds") or {}).get("steps", [])
        if len(existing) <= 1:
            defaults["thresholds"] = _pick_thresholds(p.get("title", ""))
        defaults["color"] = {"mode": "thresholds"}

    # 3. Prepend animated banner panel
    max_id = max((p["id"] for p in panels), default=100)
    banner = {
        "id": max_id + 10,
        "title": "",
        "type": "text",
        "datasource": {"type": "datasource", "uid": "-- Mixed --"},
        "gridPos": {"x": 0, "y": 0, "w": 24, "h": shift_y},
        "options": {"mode": "html", "content": banner_html},
        "fieldConfig": {"defaults": {}, "overrides": []},
        "targets": [],
        "transparent": True,
    }
    dash["panels"] = [banner] + panels
    dash["schemaVersion"] = dash.get("schemaVersion", 38) + 1

    with open(path, "w") as f:
        json.dump(dash, f, indent=2)
    print(f"  {filename}: {len(dash['panels'])} panels, banner added, stat panels enhanced")


if __name__ == "__main__":
    print("Adding animations to static dashboards...")
    upgrade_dashboard("uds_monitoring.json",  BANNER_UDS)
    upgrade_dashboard("fleet_overview.json",  BANNER_FLEET)
    upgrade_dashboard("noc_support.json",     BANNER_NOC)
    print("Done.")
