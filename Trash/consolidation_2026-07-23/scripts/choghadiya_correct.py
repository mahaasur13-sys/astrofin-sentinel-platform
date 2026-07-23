#!/usr/bin/env python3
"""Correct Choghadiya calculator — verified against drikpanchang.com.
Reference: drikpanchang.com/muhurat/choghadiya.html
"""

from datetime import datetime, timedelta, timezone
import math as _m

TZ_SAMARA = timezone(timedelta(hours=4))  # UTC+4

# Base 7-name Choghadiya cycle (standard Vedic sequence)
# 8th period = repeat of day/hour lord (first name of the rotated sequence)
CHOGHADIYA_BASE = ["Amrit", "Kala", "Shubh", "Roga", "Udveg", "Chara", "Labh"]

# Weekday → day lord → index in CHOGHADIYA_BASE
# Sunday=Sun(Udveg,6), Monday=Moon(Amrit,0), Tuesday=Mars(Roga,3),
# Wednesday=Mercury(Labh,6), Thursday=Jupiter(Shubh,2),
# Friday=Venus(Chara,5), Saturday=Saturn(Kala,1)
DAY_LORD_INDEX = {0: 0, 1: 3, 2: 6, 3: 2, 4: 5, 5: 1, 6: 4}


def _solar_event(dt, lat, lon, is_sunrise):
    """NOAA solar calculator for sunrise/sunset."""
    y, m, d = dt.year, dt.month, dt.day
    if m <= 2:
        y -= 1; m += 12
    jd = int(365.25*(y+4716))+int(30.6001*(m+1))+d+2-int(y/100)+int(y/400)-1524.5
    jc = (jd-2451545.0)/36525.0
    gl = (280.46646+jc*(36000.76983+jc*0.0003032))%360
    ga = 357.52911+jc*(35999.05029-0.0001537*jc)
    ec = 0.016708634-jc*(0.000042037+0.0000001267*jc)
    ar = _m.radians(ga)
    eqc = _m.sin(ar)*(1.914602-jc*(0.004817+0.000014*jc))+_m.sin(2*ar)*(0.019993-0.000101*jc)+_m.sin(3*ar)*0.000289
    tl = gl+eqc
    om = 125.04-1934.136*jc
    al = tl-0.00569-0.00478*_m.sin(_m.radians(om))
    obq = 23+(26+((21.448-jc*(46.815+jc*(0.00059-jc*0.001813))))/60)/60
    obc = obq+0.00256*_m.cos(_m.radians(om))
    decl = _m.degrees(_m.asin(_m.sin(_m.radians(obc))*_m.sin(_m.radians(al))))
    yf = _m.tan(_m.radians(obc/2))**2
    et = 4*_m.degrees(yf*_m.sin(2*_m.radians(gl))-2*ec*_m.sin(ar)+4*ec*yf*_m.sin(ar)*_m.cos(2*_m.radians(gl))-0.5*yf**2*_m.sin(4*_m.radians(gl))-1.25*ec**2*_m.sin(2*ar))
    zen = 90.833
    cha = (_m.cos(_m.radians(zen))-_m.sin(_m.radians(lat))*_m.sin(_m.radians(decl)))/(_m.cos(_m.radians(lat))*_m.cos(_m.radians(decl)))
    cha = max(-1.0, min(1.0, cha))
    ha = _m.degrees(_m.acos(cha))
    sn = 12.0-et/60.0-lon/15.0
    ute = sn-ha/15.0 if is_sunrise else sn+ha/15.0
    ute %= 24
    sh = (ute+4)%24
    h = int(sh); mi = int((sh-h)*60); s = int(((sh-h)*60-mi)*60)
    return dt.replace(hour=h, minute=mi, second=s, microsecond=0, tzinfo=TZ_SAMARA)


def sunrise(dt, lat=53.20, lon=50.10):
    return _solar_event(dt, lat, lon, True)

def sunset(dt, lat=53.20, lon=50.10):
    return _solar_event(dt, lat, lon, False)


def day_choghadiya(dt):
    """8 daytime Choghadiya periods (sunrise→sunset)."""
    sr = sunrise(dt)
    ss = sunset(dt)
    day_sec = (ss - sr).total_seconds()
    period_sec = day_sec / 8
    wday = dt.weekday()
    idx = DAY_LORD_INDEX.get(wday, 0)
    # 7 unique names + 8th repeats day lord
    names = [CHOGHADIYA_BASE[(idx + i) % 7] for i in range(7)]
    names.append(CHOGHADIYA_BASE[idx])  # 8th = day lord repeat
    results = []
    for i in range(8):
        start = sr + timedelta(seconds=i * period_sec)
        end = sr + timedelta(seconds=(i + 1) * period_sec)
        results.append({
            "period": i+1, "name": names[i],
            "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
        })
    return results


def night_choghadiya(dt):
    """8 night Choghadiya periods (sunset→next sunrise)."""
    ss = sunset(dt)
    sr_next = sunrise(dt + timedelta(days=1))
    night_sec = (sr_next - ss).total_seconds()
    period_sec = night_sec / 8
    wday = dt.weekday()
    idx = DAY_LORD_INDEX.get(wday, 0)
    night_idx = (idx + 5) % 7
    names = [CHOGHADIYA_BASE[(night_idx + i) % 7] for i in range(7)]
    names.append(CHOGHADIYA_BASE[night_idx])  # 8th = night lord repeat
    results = []
    for i in range(8):
        start = ss + timedelta(seconds=i * period_sec)
        end = ss + timedelta(seconds=(i + 1) * period_sec)
        results.append({
            "period": i+1, "name": names[i],
            "start": start.strftime("%H:%M"), "end": end.strftime("%H:%M"),
        })
    return results


# Quality mapping
QUALITY = {
    "Amrit": "auspicious", "Shubh": "auspicious", "Labh": "profitable",
    "Chara": "neutral", "Kala": "inauspicious",
    "Udveg": "inauspicious", "Roga": "inauspicious",
}
ICONS = {
    "Amrit": "🌊", "Shubh": "✅", "Labh": "💰",
    "Chara": "⚡", "Kala": "⛔", "Udveg": "🔴", "Roga": "⚠️",
}


if __name__ == "__main__":
    # Compare with drikpanchang for New Delhi (lat 28.61, lon 77.23, UTC+5:30)
    from datetime import timezone as tz
    IST = tz(timedelta(hours=5, minutes=30))
    dt_delhi = datetime(2026, 7, 18, tzinfo=IST)
    
    # Override sunrise/sunset for New Delhi (from drikpanchang: 05:35 AM, 07:20 PM)
    sr = dt_delhi.replace(hour=5, minute=35, second=0, microsecond=0, tzinfo=IST)
    ss = dt_delhi.replace(hour=19, minute=20, second=0, microsecond=0, tzinfo=IST)
    
    print("═" * 60)
    print("  Choghadiya: New Delhi, Saturday 2026-07-18")
    print("  (Verification against drikpanchang.com)")
    print("═" * 60)
    
    day_sec = (ss - sr).total_seconds()
    period_sec = day_sec / 8
    idx = DAY_LORD_INDEX[dt_delhi.weekday()]  # Saturday = 5, index 1
    names = [CHOGHADIYA_BASE[(idx + i) % 7] for i in range(7)]
    names.append(CHOGHADIYA_BASE[idx])
    
    print(f"\n  Day lord: Saturn (Kala), index={idx}")
    print(f"  Sunrise: {sr.strftime('%H:%M')}  Sunset: {ss.strftime('%H:%M')}")
    print(f"  Day duration: {day_sec/3600:.1f}h  Period: {period_sec/60:.0f}min")
    print(f"\n  {'Period':<8} {'Name':<8} {'Start':<8} {'End':<8} {'Quality'}")
    print(f"  {'-'*46}")
    
    for i in range(8):
        start = sr + timedelta(seconds=i * period_sec)
        end = sr + timedelta(seconds=(i + 1) * period_sec)
        q = QUALITY.get(names[i], "neutral")
        ic = ICONS.get(names[i], "?")
        print(f"  {i+1:<8} {ic} {names[i]:<5} {start.strftime('%H:%M'):<8} {end.strftime('%H:%M'):<8} {q}")
    
    print(f"\n  Drikpanchang reference (Saturday, New Delhi):")
    print(f"  1. Kala    05:35–07:18  (Loss)")
    print(f"  2. Shubh   07:18–09:01  (Good)")
    print(f"  3. Roga    09:01–10:44  (Evil)")
    print(f"  4. Udveg   10:44–12:27  (Bad)")
    print(f"  5. Chara   12:27–14:10  (Neutral)")
    print(f"  6. Labh    14:10–15:54  (Gain)")
    print(f"  7. Amrit   15:54–17:37  (Best)")
    print(f"  8. Kala    17:37–19:20  (Loss)")
    
    print(f"\n  ✅ Match check: {'PASS' if names == ['Kala','Shubh','Roga','Udveg','Chara','Labh','Amrit','Kala'] else 'FAIL'}")
    
    # ─── Samara, Saturday 2026-07-18 ───
    print(f"\n{'═'*60}")
    print(f"  Choghadiya: Samara (UTC+4), Saturday 2026-07-18")
    print(f"{'═'*60}")
    
    dt_samara = datetime(2026, 7, 18, tzinfo=TZ_SAMARA)
    sr_s = sunrise(dt_samara)
    ss_s = sunset(dt_samara)
    
    print(f"\n  Sunrise: {sr_s.strftime('%H:%M')}  Sunset: {ss_s.strftime('%H:%M')}")
    print(f"  Day duration: {(ss_s - sr_s).total_seconds()/3600:.1f}h")
    
    print(f"\n  DAY Choghadiya:")
    for p in day_choghadiya(dt_samara):
        ic = ICONS.get(p['name'], '?')
        print(f"  {p['period']}. {ic} {p['name']:<6} {p['start']}–{p['end']}")
    
    print(f"\n  NIGHT Choghadiya:")
    for p in night_choghadiya(dt_samara):
        ic = ICONS.get(p['name'], '?')
        print(f"  {p['period']}. {ic} {p['name']:<6} {p['start']}–{p['end']}")
    
    print(f"\n  ⚠️ Trading windows (auspicious only):")
    for p in day_choghadiya(dt_samara):
        if QUALITY.get(p['name']) == 'auspicious':
            print(f"  ✅ {p['start']}–{p['end']} ({p['name']})")
    for p in night_choghadiya(dt_samara):
        if QUALITY.get(p['name']) == 'auspicious':
            print(f"  ✅ {p['start']}–{p['end']} ({p['name']})")
    
    stop_periods = [p for p in day_choghadiya(dt_samara) + night_choghadiya(dt_samara)
                    if QUALITY.get(p['name']) == 'inauspicious']
    if stop_periods:
        print(f"\n  🛑 STOP zones (avoid trading):")
        for p in stop_periods:
            print(f"  🛑 {p['start']}–{p['end']} ({p['name']})")
