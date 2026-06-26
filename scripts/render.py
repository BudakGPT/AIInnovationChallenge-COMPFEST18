#!/usr/bin/env python3
"""
render.py - Turn competition.yml into the dashboard region of README.md.

Design contract:
  * competition.yml is the single source of truth.
  * Only the region between <!-- AUTO:START --> and <!-- AUTO:END --> is
    regenerated. Everything outside (the free-form canvas) is preserved, so the
    team can write freely and still get a live dashboard on every push and on a
    daily schedule.
  * The dashboard is fully self-contained: it ships its own generated SVG hero
    and progress bar (assets/), with no dependency on third-party badge hosts.

Usage:  python scripts/render.py
"""

from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required:  pip install pyyaml")

ROOT = Path(__file__).resolve().parent.parent
CONFIG = ROOT / "competition.yml"
README = ROOT / "README.md"
ASSETS = ROOT / "assets"

AUTO_START = "<!-- AUTO:START -->"
AUTO_END = "<!-- AUTO:END -->"

# Restrained, professional palette (GitHub-native neutrals).
INK = "#E6EDF3"      # primary text
MUTE = "#8B949E"     # secondary text
PANEL = "#0D1117"    # panel background
LINE = "#21262D"     # borders / track
TRACK = "#1C2128"    # progress track
DANGER = "#F85149"

# status -> (label, color). "accent" defers to the per-competition theme accent.
STATUS_META = {
    "upcoming":  ("Upcoming",  "#6E7681"),
    "active":    ("Active",    "accent"),
    "submitted": ("Submitted", "#1F6FEB"),
    "won":       ("Awarded",   "#D4A72C"),
    "lost":      ("Concluded", "#6E7681"),
    "archived":  ("Archived",  "#484F58"),
}

FONT = "'Segoe UI', -apple-system, Helvetica, Arial, sans-serif"


def load_config() -> dict:
    if not CONFIG.exists():
        sys.exit(f"Missing {CONFIG.name}")
    with CONFIG.open(encoding="utf-8") as fh:
        return yaml.safe_load(fh) or {}


def parse_date(value):
    if not value:
        return None
    if isinstance(value, dt.date):
        return value
    try:
        return dt.date.fromisoformat(str(value))
    except ValueError:
        return None


def esc(text: str) -> str:
    return (str(text).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def text_on(hex_color: str) -> str:
    """Pick readable text (dark or light) for a filled background color."""
    h = hex_color.lstrip("#")
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return "#0D1117" if luminance > 0.6 else "#FFFFFF"


def next_milestone(timeline):
    """Nearest not-done dated milestone. Returns (name, date, days_left) or None."""
    today = dt.date.today()
    pending = []
    for m in timeline or []:
        if m.get("done"):
            continue
        d = parse_date(m.get("date"))
        if d:
            pending.append((m.get("milestone", "Milestone"), d, (d - today).days))
    pending.sort(key=lambda x: x[1])
    return pending[0] if pending else None


def status_meta(status: str, accent: str):
    label, color = STATUS_META.get(status, ("Active", "accent"))
    return label, (accent if color == "accent" else color)


# ---------------------------------------------------------------------------
# Generated SVG assets
# ---------------------------------------------------------------------------

def write_header_svg(cfg: dict, accent: str) -> None:
    name = cfg.get("name", "Untitled Competition")
    organizer = cfg.get("organizer", "")
    status = cfg.get("status", "active")
    label, scolor = status_meta(status, accent)

    # Name auto-sizes so long titles do not overflow the 1200-wide canvas.
    n = len(name)
    name_size = 52 if n <= 22 else 42 if n <= 30 else 34 if n <= 42 else 28

    nxt = next_milestone(cfg.get("timeline"))
    if nxt:
        nm, nd, days = nxt
        if days < 0:
            sub = f"{nm} overdue ({nd.isoformat()})"
            sub_fill = DANGER
        elif days == 0:
            sub = f"{nm} due today ({nd.isoformat()})"
            sub_fill = DANGER
        else:
            unit = "day" if days == 1 else "days"
            sub = f"Next: {nm} in {days} {unit} ({nd.isoformat()})"
            sub_fill = MUTE
    else:
        sub = "All milestones complete"
        sub_fill = MUTE

    # Status pill, right-aligned, width estimated from text length.
    pill_text = label.upper()
    pill_w = int(len(pill_text) * 8.6) + 40
    pill_x = 1160 - pill_w

    org_line = (f'\n  <text x="64" y="74" font-family="{FONT}" font-size="20" '
                f'letter-spacing="3" fill="{MUTE}">{esc(organizer.upper())}</text>'
                if organizer else "")
    # Pull the name up a touch when there is no organizer line above it.
    name_y = 138 if organizer else 112
    rule_y = name_y + 18

    svg = f"""<svg width="1200" height="220" viewBox="0 0 1200 220" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{esc(name)}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0D1117"/>
      <stop offset="1" stop-color="#090C10"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.82" cy="0.1" r="0.7">
      <stop offset="0" stop-color="{accent}" stop-opacity="0.20"/>
      <stop offset="1" stop-color="{accent}" stop-opacity="0"/>
    </radialGradient>
    <pattern id="dots" width="24" height="24" patternUnits="userSpaceOnUse">
      <circle cx="2" cy="2" r="1.1" fill="#FFFFFF" fill-opacity="0.035"/>
    </pattern>
  </defs>
  <rect x="0.5" y="0.5" width="1199" height="219" rx="16" fill="url(#bg)" stroke="{LINE}"/>
  <rect x="0.5" y="0.5" width="1199" height="219" rx="16" fill="url(#dots)"/>
  <rect x="0.5" y="0.5" width="1199" height="219" rx="16" fill="url(#glow)"/>{org_line}
  <text x="64" y="{name_y}" font-family="{FONT}" font-size="{name_size}" font-weight="700" fill="{INK}">{esc(name)}</text>
  <rect x="64" y="{rule_y}" width="60" height="4" rx="2" fill="{accent}"/>
  <text x="64" y="192" font-family="{FONT}" font-size="18" fill="{sub_fill}">{esc(sub)}</text>
  <rect x="{pill_x}" y="40" width="{pill_w}" height="34" rx="17" fill="{scolor}"/>
  <text x="{pill_x + pill_w // 2}" y="62" font-family="{FONT}" font-size="14" font-weight="600" letter-spacing="1.5" fill="{text_on(scolor)}" text-anchor="middle">{esc(pill_text)}</text>
</svg>
"""
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "header.svg").write_text(svg, encoding="utf-8")


def write_progress_svg(done: int, total: int, accent: str) -> None:
    pct = round(100 * done / total) if total else 0
    fill_w = round(1152 * pct / 100)
    svg = f"""<svg width="1200" height="58" viewBox="0 0 1200 58" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{done} of {total} deliverables complete">
  <text x="24" y="20" font-family="{FONT}" font-size="13" font-weight="600" letter-spacing="2" fill="{MUTE}">DELIVERABLES</text>
  <text x="1176" y="20" font-family="{FONT}" font-size="13" font-weight="600" fill="{INK}" text-anchor="end">{done} / {total} &#183; {pct}%</text>
  <rect x="24" y="34" width="1152" height="10" rx="5" fill="{TRACK}"/>
  <rect x="24" y="34" width="{fill_w}" height="10" rx="5" fill="{accent}">
    <animate attributeName="width" from="0" to="{fill_w}" dur="0.9s" fill="freeze"/>
  </rect>
</svg>
"""
    ASSETS.mkdir(parents=True, exist_ok=True)
    (ASSETS / "progress.svg").write_text(svg, encoding="utf-8")


# ---------------------------------------------------------------------------
# Markdown sections
# ---------------------------------------------------------------------------

def render_gantt(timeline, nearest_name) -> str:
    if not timeline:
        return "_No timeline defined yet._"
    lines = [
        "```mermaid",
        "%%{init: {'gantt': {'barHeight': 22, 'fontSize': 13, 'sectionFontSize': 13, 'topPadding': 24}}}%%",
        "gantt",
        "    dateFormat YYYY-MM-DD",
        "    axisFormat %b %d",
        "    todayMarker stroke-width:2px,stroke:#8b949e,opacity:0.6",
        "    section Milestones",
    ]
    for i, m in enumerate(timeline, 1):
        d = parse_date(m.get("date"))
        if d is None:
            continue
        name = str(m.get("milestone", f"Milestone {i}")).replace(":", " -")
        tag = "done, " if m.get("done") else ("crit, " if m.get("milestone") == nearest_name else "")
        lines.append(f"    {name} :{tag}m{i}, {d.isoformat()}, 1d")
    lines.append("```")
    return "\n".join(lines)


def render_deliverables(deliverables) -> tuple[str, int, int]:
    items = deliverables or []
    if not items:
        return ("_No deliverables defined yet._", 0, 0)
    done = sum(1 for d in items if d.get("done"))
    rows = [f"- [{'x' if d.get('done') else ' '}] {d.get('name', 'Untitled')}" for d in items]
    return ("\n".join(rows), done, len(items))


def render_links(links) -> str:
    label_map = [
        ("registration", "Registration"),
        ("website", "Event site"),
        ("devpost", "Submission"),
        ("code", "Source code"),
        ("slides", "Slide deck"),
        ("demo", "Live demo"),
    ]
    rows = [f"| {label} | {url} |" for key, label in label_map if (url := (links or {}).get(key))]
    if not rows:
        return "_No resources linked yet._"
    return "| Resource | Link |\n| :--- | :--- |\n" + "\n".join(rows)


def render_callout(timeline) -> str:
    nxt = next_milestone(timeline)
    if not nxt:
        return "> All milestones complete."
    nm, nd, days = nxt
    if days < 0:
        return f"> **{nm}** is overdue (was due {nd.isoformat()})."
    if days == 0:
        return f"> **{nm}** is due today ({nd.isoformat()})."
    unit = "day" if days == 1 else "days"
    return f"> Next milestone: **{nm}**, {days} {unit} remaining ({nd.isoformat()})."


def build_auto_block(cfg: dict) -> str:
    theme = cfg.get("theme", {}) or {}
    accent = "#" + str(theme.get("accent", "2EA043")).lstrip("#")
    banner = theme.get("banner", "")
    timeline = cfg.get("timeline", []) or []

    write_header_svg(cfg, accent)
    deliv_md, done, total = render_deliverables(cfg.get("deliverables"))
    write_progress_svg(done, total, accent)

    hero = banner if banner else "assets/header.svg"
    nearest = next_milestone(timeline)
    gantt = render_gantt(timeline, nearest[0] if nearest else None)
    updated = dt.date.today().isoformat()

    parts = [
        AUTO_START,
        "<!-- Generated by scripts/render.py. Do not edit inside this block; edit competition.yml. -->",
        "",
        f'<p align="center"><img src="{hero}" alt="{esc(cfg.get("name", "Competition"))}" width="100%"></p>',
        "",
        render_callout(timeline),
        "",
        "## Timeline",
        "",
        gantt,
        "",
        "## Deliverables",
        "",
        '<img src="assets/progress.svg" alt="Deliverable progress" width="100%">',
        "",
        deliv_md,
        "",
        "## Resources",
        "",
        render_links(cfg.get("links")),
        "",
        f'<div align="right"><sub>Last updated {updated}</sub></div>',
        "",
        AUTO_END,
    ]
    return "\n".join(parts)


CANVAS_TEMPLATE = """

## Problem statement
_What are we solving, and why does it matter? This section is free-form and is never overwritten by automation._

## Approach
_Our solution, the architecture, and the stack._

## Demo
_Screenshots, recordings, or a link to the live demo._

## Notes
_Rules, judging criteria, ideas, and open questions the team should remember._

## Results
_Outcome and reflections. Update after judging._
"""


def splice(existing: str, auto_block: str) -> str:
    if AUTO_START in existing and AUTO_END in existing:
        pre = existing.split(AUTO_START)[0]
        post = existing.split(AUTO_END, 1)[1]
        return pre + auto_block + post
    return auto_block + "\n" + CANVAS_TEMPLATE


def main() -> None:
    cfg = load_config()
    auto_block = build_auto_block(cfg)
    existing = README.read_text(encoding="utf-8") if README.exists() else ""
    README.write_text(splice(existing, auto_block), encoding="utf-8")
    print("Rendered README.md")


if __name__ == "__main__":
    main()
