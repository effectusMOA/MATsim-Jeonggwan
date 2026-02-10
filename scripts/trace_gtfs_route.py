"""
Trace specific negative-offset route to GTFS source data
"""
import csv

gtfs_dir = "2024-TM-PT-GTFS 대중교통GTFS(2023년 기준)/202303_GTFS_DataSet"

# 1. Find trips for the negative-offset route
target_route = "BR_ACC0_3751035011"
print(f"Looking for route {target_route} in trips.txt...")

matching_trips = []
with open(f"{gtfs_dir}/trips.txt", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        if target_route in row.get("route_id", ""):
            matching_trips.append(row)
            print(f"  Found: route={row['route_id']}, trip={row['trip_id']}")

# 2. Find stop_times for these trips
if matching_trips:
    trip_ids = set(m["trip_id"] for m in matching_trips)
    print(f"\nStop times for these trips:")
    with open(f"{gtfs_dir}/stop_times.txt", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("trip_id") in trip_ids:
                print(f"  trip={row['trip_id']}, seq={row['stop_sequence']}, "
                      f"arr={row['arrival_time']}, dep={row['departure_time']}, "
                      f"stop={row['stop_id']}")

# 3. Also check a route with DECREASING offsets
# Look at routes in 정관 area (부산)
print("\n\n--- Checking 부산 bus routes (BR_2100_*) ---")
busan_routes = []
with open(f"{gtfs_dir}/routes.txt", "r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for row in reader:
        rid = row.get("route_id", "")
        if rid.startswith("BR_2100_") and len(busan_routes) < 5:
            busan_routes.append(row)
            print(f"  route={rid}, name={row.get('route_short_name','')}, type={row.get('route_type','')}")

# 4. Get GTFS stop_times for one Busan bus
if busan_routes:
    target_route_busan = busan_routes[0]["route_id"]
    print(f"\nLooking for trips of route {target_route_busan}...")
    busan_trips = []
    with open(f"{gtfs_dir}/trips.txt", "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("route_id") == target_route_busan:
                busan_trips.append(row)
    
    print(f"  Found {len(busan_trips)} trips")
    if busan_trips:
        first_trip = busan_trips[0]["trip_id"]
        print(f"\n  GTFS stop_times for trip {first_trip}:")
        with open(f"{gtfs_dir}/stop_times.txt", "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("trip_id") == first_trip:
                    print(f"    seq={row['stop_sequence']}, arr={row['arrival_time']}, "
                          f"dep={row['departure_time']}, stop={row['stop_id']}")

# 5. Now compare with MATSim transit schedule
print("\n\n--- MATSim Transit Schedule comparison ---")
import xml.etree.ElementTree as ET
tree = ET.parse("input/regional-transit-schedule.xml")
root = tree.getroot()

# Find the same Busan route
for tl in root.findall(".//transitLine"):
    line_id = tl.get("id", "")
    if busan_routes and line_id == busan_routes[0]["route_id"]:
        print(f"\nMATSim line: {line_id}")
        for route in tl.findall("transitRoute"):
            route_id = route.get("id", "")
            print(f"  Route: {route_id}")
            
            profile = route.find("routeProfile")
            if profile is not None:
                for stop in profile.findall("stop")[:15]:
                    print(f"    Stop {stop.get('refId')}: arr={stop.get('arrivalOffset')}, "
                          f"dep={stop.get('departureOffset')}")
            
            deps = route.find("departures")
            if deps is not None:
                for dep in deps.findall("departure")[:5]:
                    print(f"    Departure: id={dep.get('id')}, time={dep.get('departureTime')}")
        break

# 6. Check the GTFS conversion script if it exists
print("\n\n--- Looking for GTFS conversion script ---")
import os
for root_dir, dirs, files in os.walk("src"):
    for fname in files:
        if "gtfs" in fname.lower() or "transit" in fname.lower():
            print(f"  {os.path.join(root_dir, fname)}")

for root_dir, dirs, files in os.walk("scripts"):
    for fname in files:
        if "gtfs" in fname.lower() or "transit" in fname.lower():
            print(f"  {os.path.join(root_dir, fname)}")

print("\nDone!")
