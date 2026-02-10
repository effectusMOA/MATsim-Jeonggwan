import pandas as pd
import geopandas as gpd
import xml.etree.ElementTree as ET
from pyproj import Transformer
import os
import shutil

# Config
NETWORK_FILE = "input/regional-network-expanded.xml"
GTFS_DIR = "2024-TM-PT-GTFS 대중교통GTFS(2023년 기준)/202303_GTFS_DataSet"
OUTPUT_DIR = "input/regional-gtfs"
BUFFER_M = 500 # 500m buffer around network

print("1. Calculating Bounding Box from Network...")
tree = ET.parse(NETWORK_FILE)
root = tree.getroot()

xs = []
ys = []

# Namespace handling
ns = {'ns': 'http://www.matsim.org/files/dtd'}
# Try finding with and without namespace
nodes = root.findall('.//ns:node', ns)
if not nodes:
    nodes = root.findall('.//node')

for node in nodes:
    xs.append(float(node.get('x')))
    ys.append(float(node.get('y')))

min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)

print(f"  Network BBox (EPSG:5179): X[{min_x:.1f}, {max_x:.1f}], Y[{min_y:.1f}, {max_y:.1f}]")

# Add buffer
min_x -= BUFFER_M
max_x += BUFFER_M
min_y -= BUFFER_M
max_y += BUFFER_M

# Convert to EPSG:4326 (Lat/Lon) for GTFS filtering
transformer = Transformer.from_crs("EPSG:5179", "EPSG:4326", always_xy=True)
min_lon, min_lat = transformer.transform(min_x, min_y)
max_lon, max_lat = transformer.transform(max_x, max_y)

print(f"  Filter BBox (EPSG:4326): Lon[{min_lon:.6f}, {max_lon:.6f}], Lat[{min_lat:.6f}, {max_lat:.6f}]")

if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

print("\n2. Filtering stops.txt...")
stops = pd.read_csv(os.path.join(GTFS_DIR, "stops.txt"), dtype=str)
# Convert lat/lon to float for filtering
stops['stop_lat'] = stops['stop_lat'].astype(float)
stops['stop_lon'] = stops['stop_lon'].astype(float)

# Filter
filtered_stops = stops[
    (stops['stop_lon'] >= min_lon) & (stops['stop_lon'] <= max_lon) &
    (stops['stop_lat'] >= min_lat) & (stops['stop_lat'] <= max_lat)
].copy()

print(f"  -> Stops: {len(stops)} -> {len(filtered_stops)}")
filtered_stops.to_csv(os.path.join(OUTPUT_DIR, "stops.txt"), index=False)
valid_stop_ids = set(filtered_stops['stop_id'])

print("\n3. Filtering stop_times.txt...")
# stop_times is huge, read in chunks
chunk_size = 100000
valid_trip_ids = set()
first_chunk = True

with open(os.path.join(OUTPUT_DIR, "stop_times.txt"), 'w', encoding='utf-8', newline='') as f_out:
    for chunk in pd.read_csv(os.path.join(GTFS_DIR, "stop_times.txt"), chunksize=chunk_size, dtype=str):
        # Filter by stop_id
        filtered_chunk = chunk[chunk['stop_id'].isin(valid_stop_ids)]
        
        if not filtered_chunk.empty:
            # Collect trip_ids
            valid_trip_ids.update(filtered_chunk['trip_id'])
            
            # Write
            filtered_chunk.to_csv(f_out, header=first_chunk, index=False)
            first_chunk = False
            
print(f"  -> Found {len(valid_trip_ids)} trips visiting these stops.")

print("\n4. Filtering trips.txt...")
trips = pd.read_csv(os.path.join(GTFS_DIR, "trips.txt"), dtype=str)
filtered_trips = trips[trips['trip_id'].isin(valid_trip_ids)]
print(f"  -> Trips: {len(trips)} -> {len(filtered_trips)}")
filtered_trips.to_csv(os.path.join(OUTPUT_DIR, "trips.txt"), index=False)
valid_route_ids = set(filtered_trips['route_id'])
valid_service_ids = set(filtered_trips['service_id'])

print("\n5. Filtering routes.txt...")
routes = pd.read_csv(os.path.join(GTFS_DIR, "routes.txt"), dtype=str)
filtered_routes = routes[routes['route_id'].isin(valid_route_ids)]
print(f"  -> Routes: {len(routes)} -> {len(filtered_routes)}")
filtered_routes.to_csv(os.path.join(OUTPUT_DIR, "routes.txt"), index=False)
valid_agency_ids = set(filtered_routes['agency_id'])

print("\n6. Filtering agency.txt...")
agency = pd.read_csv(os.path.join(GTFS_DIR, "agency.txt"), dtype=str)
filtered_agency = agency[agency['agency_id'].isin(valid_agency_ids)]
print(f"  -> Agencies: {len(agency)} -> {len(filtered_agency)}")
filtered_agency.to_csv(os.path.join(OUTPUT_DIR, "agency.txt"), index=False)

print("\n7. Filtering calendar.txt (if exists)...")
if os.path.exists(os.path.join(GTFS_DIR, "calendar.txt")):
    calendar = pd.read_csv(os.path.join(GTFS_DIR, "calendar.txt"), dtype=str)
    filtered_calendar = calendar[calendar['service_id'].isin(valid_service_ids)]
    print(f"  -> Calendar: {len(calendar)} -> {len(filtered_calendar)}")
    filtered_calendar.to_csv(os.path.join(OUTPUT_DIR, "calendar.txt"), index=False)

print("Done! Sliced GTFS saved to input/jeonggwan-gtfs")
