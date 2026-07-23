#!/usr/bin/env -S uv run --python 3.12
"""Generate July 2026 Panchanga + Choghadiya calendar in HTML.

USAGE: python scripts/visualize_panchanga_calendar.py [--location LAT LON LABEL]

Uses NOAA-based solar calculations (no Swiss Ephemeris needed for Choghadiya).
Output: scripts/panchanga_calendar_july_2026.html
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, "/home/workspace")

from core.panchanga import (
    get_choghadiya,
    get_night_choghadiya,
    get_muhurta_score,
    _get_tz_offset_hours,
    _sunrise,
    _sunset,
)

UTC3 = timezone(timedelta(hours=3))


def generate_july_calendar(lat: float, lon: float, label: str) -> str:
    tds = []
    yesterday_night = []
    today_day = []
    today_night = []
    muhurta_scores = []

    for day in range(1, 32):
        dt_samara = datetime(2026, 7, day, 12, 0, 0, tzinfo=UTC3)
        dt_key = dt_samara.strftime("%d.%m")

        # Day + night Choghadiya
        day_chog = get_choghadiya(dt_samara, lat, lon)
        night_chog = get_night_choghadiya(dt_samara, lat, lon)
        all_chog = day_chog + night_chog

        sunrise = _sunrise(dt_samara, lat, lon)
        sunset = _sunset(dt_samara, lat, lon)

        tds.append({
            "date": dt_key,
            "sunrise": sunrise.strftime("%H:%M"),
            "sunset": sunset.strftime("%H:%M"),
            "day_periods": [{
                "period": p["period"],
                "name": p["name"],
                "start": p["start"],
                "end": p["end"],
                "quality": p["quality"],
                "icon": p.get("icon", ""),
                "recommended": p.get("recommended", False),
            } for p in day_chog],
            "night_periods": [{
                "period": p["period"],
                "name": p["name"],
                "start": p["start"],
                "end": p["end"],
                "quality": p["quality"],
                "icon": p.get("icon", ""),
                "recommended": p.get("recommended", False),
            } for p in night_chog],
            "muhurta_scores": [{
                "period": p["period"],
                "name": p["name"],
                "score": get_muhurta_score(p["name"], None, None, None).get("score", 50),
            } for p in all_chog],
            "best_periods": [p for p in all_chog if p.get("recommended")],
        })

    # Build HTML
    quality_colors = {
        "auspicious": "#e6ffe6",
        "neutral": "#fff8e1",
        "evil": "#ffe6e6",
        "waste": "#f3e5f5",
    }
    quality_emoji = {
        "Amrit": "🍯", "Shubh": "✨", "Labh": "💰",
        "Chara": "🔄", "Roga": "🤒", "Kaal": "⛔",
        "Udveg": "😰", "Vyaghata": "⚠️", "Mando": "🐌",
    }

    periods_html = ""
    for td in tds:
        cell = "<td class='day-cell'>"
        cell += f"<div class='date'>{td['date']}</div>"
        cell += f"<div class='sun'>🌅{td['sunrise']} 🌇{td['sunset']}</div>"
        for p in td["day_periods"]:
            color = quality_colors.get(p["quality"], "#fff")
            emoji = quality_emoji.get(p["name"], "")
            rec = "✅" if p["recommended"] else ""
            cell += f"<div class='slot' style='background:{color}'>{emoji} {p['start']} {p['name']} {rec}</div>"
        cell += "<div class='night-label'>🌙 Ночь</div>"
        for p in td["night_periods"]:
            color = quality_colors.get(p["quality"], "#fff")
            emoji = quality_emoji.get(p["name"], "")
            rec = "✅" if p["recommended"] else ""
            cell += f"<div class='slot' style='background:{color}'>{emoji} {p['start']} {p['name']} {rec}</div>"
        cell += "</td>"
        periods_html += cell

    html = f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Panchanga Calendar — July 2026 — {label}</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #1a1a2e; color: #eee; margin: 0; padding: 16px; }}
  h1 {{ text-align: center; color: #f0c040; }}
  .subtitle {{ text-align: center; color: #aaa; margin-bottom: 24px; }}
  table {{ border-collapse: collapse; width: 100%; }}
  .day-cell {{ border: 1px solid #333; padding: 6px; vertical-align: top; min-width: 280px; }}
  .date {{ font-weight: bold; font-size: 1.1em; margin-bottom: 4px; color: #f0c040; }}
  .sun {{ font-size: 0.85em; color: #aaa; margin-bottom: 6px; }}
  .slot {{ font-size: 0.78em; padding: 2px 4px; margin: 1px 0; border-radius: 3px; }}
  .night-label {{ margin-top: 8px; font-weight: bold; color: #a0a0ff; font-size: 0.85em; }}
  .legend {{ display: flex; gap: 16px; flex-wrap: wrap; justify-content: center; margin-bottom: 20px; }}
  .legend-item {{ display: flex; align-items: center; gap: 4px; font-size: 0.85em; }}
  .legend-swatch {{ width: 16px; height: 16px; border-radius: 3px; border: 1px solid #555; }}
</style>
</head>
<body>
<h1>🗓️ Panchanga Calendar — July 2026</h1>
<p class="subtitle">{label} (lat={lat}, lon={lon}) · Choghadiya days + nights · NOAA solar calc</p>
<div class="legend">
  <div class="legend-item"><div class="legend-swatch" style="background:#e6ffe6"></div> Благоприятный</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#fff8e1"></div> Нейтральный</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#ffe6e6"></div> Неблагоприятный</div>
  <div class="legend-item"><div class="legend-swatch" style="background:#f3e5f5"></div> Пустой (waste)</div>
  <div class="legend-item">✅ — recommended for trading</div>
</div>
<table><tr>{periods_html}</tr></table>
<p style="text-align:center; margin-top:24px; color:#666; font-size:0.8em">
  Generated by AstroFin Sentinel V5 · core/panchanga.py · NOAA solar calculations
</p>
</body>
</html>"""

    out = "scripts/panchanga_calendar_july_2026.html"
    with open(out, "w") as f:
        f.write(html)
    return out


def main():
    p = argparse.ArgumentParser(description="Generate Panchanga calendar")
    p.add_argument("--location", nargs=3, metavar=("LAT", "LON", "LABEL"),
                   default=[25.20, 55.27, "Dubai"])
    args = p.parse_args()
    lat, lon = float(args.location[0]), float(args.location[1])
    label = args.location[2]
    path = generate_july_calendar(lat, lon, label)
    print(f"✅ Calendar saved to {path}")
    print(f"   Open: file://{path}")


if __name__ == "__main__":
    main()
