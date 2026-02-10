"""
Verify PT Route Existence between Gap Clusters
Checks if there's a valid PT path connecting the problematic O/D pairs
by analyzing the transit schedule (routes, stops, and connections).
"""
import xml.etree.ElementTree as ET
from scipy.spatial import cKDTree
import pandas as pd
import json

# Configuration
TRANSIT_SCHEDULE_FILE = "input/regional-transit-schedule.xml"
GAP_CLUSTERS_FILE = "output/gap_clusters_od.json"

print("1. Loading Transit Schedule...")
tree = ET.parse(TRANSIT_SCHEDULE_FILE)
root = tree.getroot()

# Load stops
stops = []
for stop in root.find('transitStops').findall('stopFacility'):
    stops.append({
        'id': stop.get('id'),
        'x': float(stop.get('x')),
        'y': float(stop.get('y'))
    })
df_stops = pd.DataFrame(stops)
stops_tree = cKDTree(df_stops[['x', 'y']].values)
print(f"   Loaded {len(df_stops)} stops.")

# Build stop-to-routes mapping
print("2. Building Stop-to-Routes Mapping...")
stop_routes = {}  # stop_id -> list of route_ids
route_stops = {}  # route_id -> list of stop_ids (ordered)

transit_lines = root.find('transitSchedule') if root.find('transitSchedule') else root
for line in transit_lines.findall('.//transitLine'):
    line_id = line.get('id')
    for route in line.findall('transitRoute'):
        route_id = f"{line_id}_{route.get('id')}"
        route_stop_list = []
        for rs in route.find('routeProfile').findall('stop'):
            stop_id = rs.get('refId')
            route_stop_list.append(stop_id)
            if stop_id not in stop_routes:
                stop_routes[stop_id] = []
            stop_routes[stop_id].append(route_id)
        route_stops[route_id] = route_stop_list

print(f"   Indexed {len(route_stops)} routes across {len(stop_routes)} unique stops with service.")

# Load cluster centroids
print("3. Loading Gap Clusters...")
with open(GAP_CLUSTERS_FILE, 'r', encoding='utf-8') as f:
    clusters = json.load(f)

origins = clusters['origins']
destinations = clusters['destinations']

# Function to find nearest stop with service
def find_nearest_served_stop(x, y, k=5):
    dists, idxs = stops_tree.query([x, y], k=k)
    for dist, idx in zip(dists, idxs):
        stop_id = df_stops.iloc[idx]['id']
        if stop_id in stop_routes:
            return stop_id, dist, stop_routes[stop_id]
    return None, None, []

# Check connectivity
print("\n" + "="*60)
print("4. PT ROUTE CONNECTIVITY CHECK")
print("="*60)

results = []

for o in origins:
    o_stop, o_dist, o_routes = find_nearest_served_stop(o['x'], o['y'])
    print(f"\n[Origin O{o['id']}] ({o['x']:.0f}, {o['y']:.0f})")
    print(f"  Nearest Served Stop: {o_stop} at {o_dist:.0f}m")
    print(f"  Routes Serving: {len(o_routes)} routes")
    
    for d in destinations:
        d_stop, d_dist, d_routes = find_nearest_served_stop(d['x'], d['y'])
        
        # Check direct connection (same route serves both)
        common_routes = set(o_routes) & set(d_routes)
        
        # Check 1-transfer connection
        o_reachable_stops = set()
        for route in o_routes:
            o_reachable_stops.update(route_stops.get(route, []))
        
        d_reachable_stops = set()
        for route in d_routes:
            d_reachable_stops.update(route_stops.get(route, []))
        
        # Transfer stops = stops reachable from O that have routes going to D
        transfer_stops = set()
        for stop in o_reachable_stops:
            if stop in stop_routes:
                for route in stop_routes[stop]:
                    if any(s in d_reachable_stops for s in route_stops.get(route, [])):
                        transfer_stops.add(stop)
        
        result = {
            'origin': f"O{o['id']}",
            'destination': f"D{d['id']}",
            'o_stop': o_stop,
            'd_stop': d_stop,
            'direct_routes': len(common_routes),
            'transfer_possible': len(transfer_stops) > 0,
            'transfer_stops_count': len(transfer_stops) if transfer_stops else 0
        }
        results.append(result)
        
        if common_routes:
            print(f"  -> D{d['id']}: ✅ DIRECT connection ({len(common_routes)} common routes)")
        elif transfer_stops:
            print(f"  -> D{d['id']}: ⚠️ 1-TRANSFER possible via {len(transfer_stops)} stops")
        else:
            print(f"  -> D{d['id']}: ❌ NO CONNECTION FOUND")

# Summary
print("\n" + "="*60)
print("5. SUMMARY")
print("="*60)
df_results = pd.DataFrame(results)
print(df_results.to_string(index=False))

# Save results
with open('output/pt_route_check_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("\nSaved to output/pt_route_check_results.json")
