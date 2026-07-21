#!/usr/bin/env python3
"""Sprint 6: Vedic Election Calculator for AstroFin Sentinel.

Usage:
    cd /home/workspace/astrofin-sentinel-platform
    source venv/bin/activate
    python tools/run_election.py                     # today, Dubai TZ
    python tools/run_election.py 2026-07-19          # specific date
    python tools/run_election.py 2026-07-19 Samara   # Dubai default
"""

import sys
from datetime import datetime, timezone, timedelta

SYM = "━" * 68

def run_election(date_str: str | None = None):
    from core.panchanga import calculate_panchanga
    from trading.vedic.nakshatra_risk import (
        get_nakshatra_multiplier, get_election_grade,
        is_dangerous_nakshatra, is_favorable_nakshatra,
    )

    if date_str:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    else:
        dt = datetime.now()

    dt = dt.replace(hour=6, minute=15, tzinfo=timezone(timedelta(hours=4)))
    p = calculate_panchanga(dt)

    nak = p["nakshatra"]
    tit = p["tithi"]
    yog = p["yoga"]
    kar = p["karana"]
    ms = p["muhurta_score"]

    N = nak["name"]
    mult = get_nakshatra_multiplier(N)
    grade = get_election_grade(N)
    base_risk = 0.05
    risk_pct = round(base_risk * mult * (0.85 if mult > 1.15 else 1.0), 3)

    print(f"\n{SYM}")
    print(f"  🎯 ASTROFIN ELECTION — {dt.strftime('%d.%m.%Y')}")
    print(f"{SYM}")
    print(f"  Nakshatra:  {N} (#{nak['number']}, Lord {nak['lord']}, Pada {nak['pada']})")
    print(f"  Tithi:      {tit['name']} ({'Shukla' if tit['is_waxing'] else 'Krishna'})")
    print(f"  Yoga:       {yog['name']} (#{yog['number']})")
    print(f"  Karana:     {kar['name']}")
    print(f"  Moon Rashi: {p['moon_rashi']}")
    print(f"  Muhurta:    {ms['score']}/100 — {ms['verdict']}")
    print()
    print(f"  Risk mult:  ×{mult:.2f}  |  Grade: {grade.value}")
    print(f"  Danger:     {'⚠️  YES' if is_dangerous_nakshatra(N) else '✅ No'}")
    print(f"  Favorable:  {'✅ YES' if is_favorable_nakshatra(N) else '—'}")
    print(f"  Position:   {risk_pct*100:.1f}% risk")
    print(f"  Stop-loss:  ×{1.2 if mult > 1.15 else 1.0}")

    print(f"\n  🕐 CHOGHADIYA (Dubai +4 UTC):")
    for c in p["choghadiya"]:
        bar = "▐" if c["recommended"] else " "
        print(f"  {bar} {c['start']}–{c['end']}  {c['icon']} {c['name']:<8s} ({c['quality']})")

    verdicts = {
        "Excellent": "🟢 ОТЛИЧНЫЙ день для входа",
        "Good": "🟢 ХОРОШИЙ день",
        "Average": "🟡 СРЕДНИЙ — осторожно",
        "Poor": "🔴 ПЛОХОЙ — HOLD",
    }
    print(f"\n  {verdicts.get(ms['verdict'], ms['verdict'])}")
    print(f"{SYM}\n")

if __name__ == "__main__":
    run_election(sys.argv[1] if len(sys.argv) > 1 else None)
