"""
Check decreasing offsets pattern in transit schedule
"""
import xml.etree.ElementTree as ET

tree = ET.parse("input/regional-transit-schedule.xml")
root = tree.getroot()

count = 0
for tl in root.findall(".//transitLine"):
    line_id = tl.get("id", "")
    for route in tl.findall("transitRoute"):
        route_id = route.get("id", "")
        profile = route.find("routeProfile")
        if profile is None:
            continue
        
        stops = profile.findall("stop")
        if len(stops) < 5:
            continue
        
        prev_dep = None
        has_decrease = False
        decrease_at = -1
        for idx, stop in enumerate(stops):
            dep = stop.get("departureOffset", "")
            if dep:
                parts = dep.split(":")
                sec = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                if prev_dep is not None and sec < prev_dep:
                    has_decrease = True
                    decrease_at = idx
                    break
                prev_dep = sec
        
        if has_decrease and count < 3:
            count += 1
            print(f"=== DECREASING OFFSET Route: {line_id} / {route_id} ===")
            
            deps = route.find("departures")
            if deps is not None:
                for dep in deps.findall("departure")[:3]:
                    print(f"  Departure: {dep.get('departureTime')}")
            
            for idx, stop in enumerate(stops[:30]):
                ref = stop.get("refId")
                arr = stop.get("arrivalOffset", "")
                dep_off = stop.get("departureOffset", "")
                marker = " <-- DECREASE!" if idx == decrease_at else ""
                print(f"  [{idx:2d}] Stop {ref}: arr={arr}, dep={dep_off}{marker}")
            if len(stops) > 30:
                print(f"  ... ({len(stops)} stops total)")
            print()

# Also check format_time with large offsets
print("=== format_time bug demo ===")
def format_time(seconds):
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    if h >= 24: h = h % 24
    return f"{h:02d}:{m:02d}:{s:02d}"

# This simulates a 3-hour bus route starting at 23:00
# Stop offsets: 0, 3600, 7200, 10800
# Stop 4 offset = 10800 sec = 3:00:00 (correct)
# But the departure time = 23:00 + 3:00 = 26:00 in GTFS
# format_time wraps 26 -> 02, destroying the offset

# Actually, offsets are relative to departure time, not absolute.
# The issue is different: GTFS uses absolute times, conversion subtracts start
# If a trip pattern SHARES the same route with different trips,
# the offsets are computed from the FIRST trip's start time

# Let's check if the decreasing pattern is from format_time wrapping
for i in range(25):
    hr = i
    print(f"  {hr}h offset -> format_time: {format_time(hr * 3600)}")
print()

# Check the GTFS for a concrete example
# Look at what times the GTFS has for the route_id matching the first decreasing line
print("=== Verifying GTFS source for comparison ===")
# Read first decreasing route's line_id as GTFS route_id
import csv

# Check the route BR_ACC0_21310023 which has 90 stops and 3h duration
print("\nChecking BR_ACC0_21310023 in GTFS...")
gtfs_dir = "2024-TM-PT-GTFS 대중교통GTFS(2023년 기준)/202303_GTFS_DataSet"

# Find trip ids
trip_ids = set()
with open(f"{gtfs_dir}/trips.txt", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row.get("route_id") == "BR_ACC0_21310023":
            trip_ids.add(row["trip_id"])
            
print(f"  Found {len(trip_ids)} trips for route BR_ACC0_21310023")

# Find stop_times for first trip
if trip_ids:
    first_trip = sorted(trip_ids)[0]
    print(f"  Stop times for trip {first_trip}:")
    with open(f"{gtfs_dir}/stop_times.txt", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("trip_id") == first_trip:
                print(f"    seq={row['stop_sequence']}, arr={row['arrival_time']}, "
                      f"dep={row['departure_time']}, stop={row['stop_id']}")
