import xml.etree.ElementTree as ET
import json

# Configuration
TRANSIT_SCHEDULE_FILE = "input/regional-transit-schedule.xml"

# Target stops from the PT route check
target_stops = [
    "BS_TAGO_BSB212780101",  # O1
    "BS_TAGO_BSB500600000",  # D2 - the problematic one
    "BS_TAGO_BSB193780301",  # D1
    "BS_TAGO_GHB1820"        # D3
]

print("Loading Transit Schedule...")
tree = ET.parse(TRANSIT_SCHEDULE_FILE)
root = tree.getroot()

# Build stop-to-routes mapping
stop_routes = {}
route_count = 0

for line in root.findall('.//transitLine'):
    line_id = line.get('id')
    for route in line.findall('transitRoute'):
        route_id = f"{line_id}_{route.get('id')}"
        route_count += 1
        for rs in route.find('routeProfile').findall('stop'):
            stop_id = rs.get('refId')
            if stop_id not in stop_routes:
                stop_routes[stop_id] = []
            stop_routes[stop_id].append(route_id)

print(f"Indexed {route_count} routes.")
print(f"Total stops with service: {len(stop_routes)}")

print("\n" + "="*60)
print("STOP ANALYSIS:")
print("="*60)

results = {}
for stop_id in target_stops:
    routes = stop_routes.get(stop_id, [])
    results[stop_id] = {
        "route_count": len(routes),
        "sample_routes": routes[:5] if routes else []
    }
    print(f"\n{stop_id}:")
    print(f"  Routes serving this stop: {len(routes)}")
    if routes:
        print(f"  Sample routes: {routes[:3]}")
    else:
        print("  >>> NO ROUTES SERVE THIS STOP! <<<")

with open('output/stop_routes_analysis.json', 'w') as f:
    json.dump(results, f, indent=2)
print("\nSaved to output/stop_routes_analysis.json")

