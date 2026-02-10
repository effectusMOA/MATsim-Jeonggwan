"""
GTFS Data Quality Verification for Jeonggwan Area
Checks:
1. How many stops are in the Jeonggwan bounding box
2. What routes serve those stops
3. Route names to identify bus types (express, local, etc.)
"""
import csv
import json
from collections import Counter

# Jeonggwan approximate bounding box (WGS84)
# Jeonggwan-eup, Gijang-gun, Busan: approximately 35.31°N, 129.18°E
JEONGGWAN_BBOX = {
    'min_lat': 35.28,   # South
    'max_lat': 35.35,   # North
    'min_lon': 129.15,  # West
    'max_lon': 129.22   # East
}

print("="*60)
print("GTFS DATA QUALITY VERIFICATION - JEONGGWAN AREA")
print("="*60)

# 1. Load stops and filter by Jeonggwan area
print("\n1. Loading stops in Jeonggwan area...")
jeonggwan_stops = []
with open('input/regional-gtfs/stops.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        try:
            lat, lon = float(row['stop_lat']), float(row['stop_lon'])
            if (JEONGGWAN_BBOX['min_lat'] <= lat <= JEONGGWAN_BBOX['max_lat'] and
                JEONGGWAN_BBOX['min_lon'] <= lon <= JEONGGWAN_BBOX['max_lon']):
                jeonggwan_stops.append({
                    'stop_id': row['stop_id'],
                    'stop_name': row.get('stop_name', 'Unknown'),
                    'lat': lat, 'lon': lon
                })
        except:
            pass


print(f"   Found {len(jeonggwan_stops)} stops in Jeonggwan area")
if jeonggwan_stops:
    print(f"   Sample stop names: {[s['stop_name'] for s in jeonggwan_stops[:5]]}")

# 2. Find routes serving Jeonggwan stops
print("\n2. Finding routes serving Jeonggwan stops...")
jeonggwan_stop_ids = set(s['stop_id'] for s in jeonggwan_stops)

# Load stop_times to find trips that stop in Jeonggwan
trip_ids_in_jeonggwan = set()
print("   Reading stop_times.txt (this may take a while)...")
with open('input/regional-gtfs/stop_times.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['stop_id'] in jeonggwan_stop_ids:
            trip_ids_in_jeonggwan.add(row['trip_id'])

print(f"   Found {len(trip_ids_in_jeonggwan)} trips stopping in Jeonggwan")

# 3. Load trips to get route_ids
print("\n3. Mapping trips to routes...")
route_ids_in_jeonggwan = set()
with open('input/regional-gtfs/trips.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['trip_id'] in trip_ids_in_jeonggwan:
            route_ids_in_jeonggwan.add(row['route_id'])

print(f"   Found {len(route_ids_in_jeonggwan)} unique routes serving Jeonggwan")

# 4. Load route details
print("\n4. Route details:")
routes_info = []
with open('input/regional-gtfs/routes.txt', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if row['route_id'] in route_ids_in_jeonggwan:
            routes_info.append({
                'route_id': row['route_id'],
                'short_name': row.get('route_short_name', ''),
                'long_name': row.get('route_long_name', ''),
                'type': row.get('route_type', '')
            })

# Categorize by route type
route_types = Counter(r['type'] for r in routes_info)
print(f"   Route types: {dict(route_types)}")
print(f"   (Type 3=Bus, 2=Rail, 1=Metro, 0=Tram)")

print("\n5. Sample routes serving Jeonggwan:")
for r in routes_info[:15]:
    print(f"   {r['short_name']:10} | {r['long_name'][:40]}")

# Save results
results = {
    'jeonggwan_stops_count': len(jeonggwan_stops),
    'trips_count': len(trip_ids_in_jeonggwan),
    'routes_count': len(route_ids_in_jeonggwan),
    'route_types': dict(route_types),
    'routes': routes_info
}

with open('output/gtfs_jeonggwan_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved detailed results to output/gtfs_jeonggwan_analysis.json")
