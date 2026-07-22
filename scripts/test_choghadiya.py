"""Test Choghadiya for 2026-07-18 (Saturday) in Samara and compare with Drik Panchang."""
import sys
sys.path.insert(0, '/home/workspace')
from datetime import datetime, timezone, timedelta
from core.panchanga import get_choghadiya, get_night_choghadiya

# Samara, Saturday 2026-07-18
tz = timezone(timedelta(hours=4))
lat, lon = 53.20, 50.10

dt = datetime(2026, 7, 18, 12, 0, 0, tzinfo=tz)
print(f"Location: Samara ({lat}°N, {lon}°E)")
print(f"Date: {dt.strftime('%A, %Y-%m-%d')}")
print(f"Timezone: UTC+4")
print()

day = get_choghadiya(dt, lat, lon)
print("=== DAY CHOGHADIYA (Samara, Saturday) ===")
print(f"{'Period':<8} {'Start':<8} {'End':<8} {'Name':<12} {'Quality':<12}")
print("-" * 52)
for p in day:
    print(f"{p['period']:<8} {p['start']:<8} {p['end']:<8} {p['name']:<12} {p['quality']:<12}")

print()
night = get_night_choghadiya(dt, lat, lon)
print("=== NIGHT CHOGHADIYA (Samara, Saturday) ===")
print(f"{'Period':<8} {'Start':<8} {'End':<8} {'Name':<12} {'Quality':<12}")
print("-" * 52)
for p in night:
    print(f"{p['period']:<8} {p['start']:<8} {p['end']:<8} {p['name']:<12} {p['quality']:<12}")

print()
print("=== COMPARE WITH DRIK PANCHANG (Saturday, Samara) ===")
print("Expected day order: Udveg, Chara, Labh, Amrit, Kala, Shubh, Roga, Udveg")
print("Expected night order: Day1:Kala→Night1:Shubh (via +5 rule)")
