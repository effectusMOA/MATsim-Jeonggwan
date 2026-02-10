import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import math
from datetime import datetime, timedelta
from pyproj import Transformer
import networkx as nx

# Configurable paths and parameters
GTFS_DIR = "input/regional-gtfs"
NETWORK_FILE = "input/regional-network-expanded.xml"
OUTPUT_SCHEDULE = "input/regional-transit-schedule.xml"
OUTPUT_VEHICLES = "input/regional-transit-vehicles.xml"
DATE_FILTER = "20230315" # Wednesday

# Mode Mapping
ROUTE_TYPE_MAP = {
    '0': 'bus',
    '1': 'subway',
    '2': 'ferry',
    '3': 'bus', # Intercity bus -> bus
    '4': 'train',
    '5': 'bus', # Airport bus -> bus
    '6': 'train', # KTX -> train
    '7': 'pt', # Air -> pt
}

VEHICLE_TYPES = {
    'bus': {'capacity': 80, 'length': 12.0, 'width': 2.5},
    'subway': {'capacity': 300, 'length': 40.0, 'width': 3.0},
    'train': {'capacity': 500, 'length': 100.0, 'width': 3.0},
    'ferry': {'capacity': 200, 'length': 30.0, 'width': 5.0},
    'pt': {'capacity': 100, 'length': 20.0, 'width': 3.0}
}

def format_time(seconds):
    """Format seconds as HH:MM:SS. Handles >24h offsets (no wrapping)."""
    if seconds < 0:
        seconds = 0  # Clamp negative offsets to zero
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    # Do NOT wrap at 24h — MATSim offsets can legitimately exceed 24 hours
    return f"{h:02d}:{m:02d}:{s:02d}"

def parse_gtfs_time(t_str):
    parts = list(map(int, t_str.split(':')))
    return parts[0] * 3600 + parts[1] * 60 + parts[2]

print("1. Loading Network for Stop Mapping...")
tree = ET.parse(NETWORK_FILE)
root = tree.getroot()

links = []
nodes = {}
link_info = {}  # Store from/to nodes for each link
G = nx.DiGraph()  # Network graph for routing

ns = {'ns': 'http://www.matsim.org/files/dtd'}
xml_nodes = root.findall('.//ns:node', ns)
if not xml_nodes:
    xml_nodes = root.findall('.//node')

for node in xml_nodes:
    nid = node.get('id')
    x = float(node.get('x'))
    y = float(node.get('y'))
    nodes[nid] = (x, y)
    G.add_node(nid)

xml_links = root.findall('.//ns:link', ns)
if not xml_links:
    xml_links = root.findall('.//link')

for link in xml_links:
    lid = link.get('id')
    from_node = link.get('from')
    to_node = link.get('to')
    modes = link.get('modes', 'car')
    length = float(link.get('length', 1000))
    
    if from_node in nodes and to_node in nodes:
        fx, fy = nodes[from_node]
        tx, ty = nodes[to_node]
        cx = (fx + tx) / 2
        cy = (fy + ty) / 2
        links.append({'id': lid, 'x': cx, 'y': cy, 'modes': modes})
        link_info[lid] = {'from': from_node, 'to': to_node, 'length': length}
        # Add edge to graph with link_id as attribute
        G.add_edge(from_node, to_node, link_id=lid, weight=length)

print(f"  -> Loaded {len(links)} links.")
print(f"  -> Graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")

def find_route_between_links(from_link_id, to_link_id):
    """Calculate the sequence of link IDs to get from one link to another."""
    if from_link_id == to_link_id:
        return []
    
    from_info = link_info.get(from_link_id)
    to_info = link_info.get(to_link_id)
    
    if not from_info or not to_info:
        return None
    
    # Route from the end of from_link to the start of to_link
    start_node = from_info['to']
    end_node = to_info['from']
    
    if start_node == end_node:
        # Directly connected
        return []
    
    try:
        path_nodes = nx.shortest_path(G, start_node, end_node, weight='weight')
        # Convert node path to link path
        route_links = []
        for i in range(len(path_nodes) - 1):
            edge_data = G.get_edge_data(path_nodes[i], path_nodes[i+1])
            if edge_data:
                route_links.append(edge_data['link_id'])
        return route_links
    except nx.NetworkXNoPath:
        return None

def find_nearest_link(x, y):
    min_dist = float('inf')
    best_link = None
    
    for link in links:
        dist = (link['x'] - x)**2 + (link['y'] - y)**2
        if dist < min_dist:
            min_dist = dist
            best_link = link['id']
            
    return best_link

print("\n2. Loading GTFS Data...")
stops = pd.read_csv(os.path.join(GTFS_DIR, "stops.txt"), dtype=str)
routes = pd.read_csv(os.path.join(GTFS_DIR, "routes.txt"), dtype=str)
trips = pd.read_csv(os.path.join(GTFS_DIR, "trips.txt"), dtype=str)
stop_times = pd.read_csv(os.path.join(GTFS_DIR, "stop_times.txt"), dtype=str)
# Bug fix: stop_sequence must be numeric for correct sorting ("10" < "2" as strings!)
stop_times['stop_sequence'] = stop_times['stop_sequence'].astype(float)
if os.path.exists(os.path.join(GTFS_DIR, "calendar.txt")):
    calendar = pd.read_csv(os.path.join(GTFS_DIR, "calendar.txt"), dtype=str)
else:
    calendar = pd.DataFrame(columns=['service_id', 'start_date', 'end_date', 'wednesday'])

transformer = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)

print("\n3. Processing Stops...")
stop_map = {} 
root_sched = ET.Element('transitSchedule')
stops_elem = ET.SubElement(root_sched, 'transitStops')

for idx, row in stops.iterrows():
    sid = row['stop_id']
    lon = float(row['stop_lon'])
    lat = float(row['stop_lat'])
    x, y = transformer.transform(lon, lat)
    
    link_id = find_nearest_link(x, y)
    
    stop_map[sid] = {'x': x, 'y': y, 'linkId': link_id}
    
    stop_fac = ET.SubElement(stops_elem, 'stopFacility')
    stop_fac.set('id', sid)
    stop_fac.set('x', f"{x:.1f}")
    stop_fac.set('y', f"{y:.1f}")
    stop_fac.set('linkRefId', link_id)
    stop_fac.set('name', row.get('stop_name', ''))

print(f"  -> Processed {len(stop_map)} stops.")

print("\n4. Processing Lines & Routes...")
active_services = set()
if not calendar.empty:
    for idx, row in calendar.iterrows():
        if row['start_date'] <= DATE_FILTER <= row['end_date']:
            if row.get('wednesday') == '1':
                active_services.add(row['service_id'])
else:
    active_services = set(trips['service_id'].unique())

print(f"  -> Found {len(active_services)} active services.")

active_trips = trips[trips['service_id'].isin(active_services)]
print(f"  -> Active trips: {len(active_trips)}")

grouped_routes = active_trips.groupby('route_id')

vehicle_counts = {k: 0 for k in VEHICLE_TYPES.keys()}
used_vehicle_ids = []

for route_id, group in grouped_routes:
    route_info = routes[routes['route_id'] == route_id].iloc[0]
    route_type_code = route_info['route_type']
    mode = ROUTE_TYPE_MAP.get(route_type_code, 'bus')
    
    line_elem = ET.SubElement(root_sched, 'transitLine')
    line_elem.set('id', route_id)
    line_elem.set('name', route_info.get('route_short_name', route_id))
    
    trip_ids = group['trip_id'].tolist()
    relevant_st = stop_times[stop_times['trip_id'].isin(trip_ids)].sort_values(['trip_id', 'stop_sequence'])
    
    trip_patterns = {}
    trip_starts = {}
    
    for tid, t_st in relevant_st.groupby('trip_id'):
        stops_seq = tuple(t_st['stop_id'].tolist())
        if stops_seq not in trip_patterns:
            trip_patterns[stops_seq] = []
        trip_patterns[stops_seq].append(tid)
        trip_starts[tid] = parse_gtfs_time(t_st.iloc[0]['departure_time'])

    pattern_idx = 0
    for stops_seq, tids in trip_patterns.items():
        pattern_idx += 1
        route_xml_id = f"{route_id}_{pattern_idx}"
        
        tr_route = ET.SubElement(line_elem, 'transitRoute')
        tr_route.set('id', route_xml_id)
        ET.SubElement(tr_route, 'transportMode').text = mode
        
        template_tid = tids[0]
        template_st = relevant_st[relevant_st['trip_id'] == template_tid]
        start_time_sec = trip_starts[template_tid]
        
        profile = ET.SubElement(tr_route, 'routeProfile')
        route_links = ET.SubElement(tr_route, 'route')
        
        # First pass: collect stop info and build route profile
        # Bug fix: ensure offsets are non-negative and monotonically increasing
        stop_link_ids = []
        prev_dep_offset = 0
        for _, st_row in template_st.iterrows():
            arr_sec = parse_gtfs_time(st_row['arrival_time'])
            dep_sec = parse_gtfs_time(st_row['departure_time'])
            
            arr_offset = max(0, arr_sec - start_time_sec)
            dep_offset = max(0, dep_sec - start_time_sec)
            
            # Ensure monotonically increasing: each stop must not be before the previous
            if arr_offset < prev_dep_offset:
                arr_offset = prev_dep_offset
            if dep_offset < arr_offset:
                dep_offset = arr_offset
            
            stop_ref = ET.SubElement(profile, 'stop')
            stop_ref.set('refId', st_row['stop_id'])
            stop_ref.set('arrivalOffset', format_time(arr_offset))
            stop_ref.set('departureOffset', format_time(dep_offset))
            stop_ref.set('awaitDeparture', 'true')
            
            prev_dep_offset = dep_offset
            
            lid = stop_map[st_row['stop_id']]['linkId']
            stop_link_ids.append(lid)
        
        # Second pass: calculate full route with intermediate links
        full_route = []
        if stop_link_ids:
            full_route.append(stop_link_ids[0])  # Start with first stop link
            
            for i in range(len(stop_link_ids) - 1):
                from_lid = stop_link_ids[i]
                to_lid = stop_link_ids[i + 1]
                
                if from_lid == to_lid:
                    continue
                
                # Calculate path between links
                intermediate = find_route_between_links(from_lid, to_lid)
                
                if intermediate is not None:
                    # Add all intermediate links in order
                    for ilink in intermediate:
                        full_route.append(ilink)
                    # Add destination link
                    full_route.append(to_lid)
                else:
                    # No path found, just add the target link (will cause warning in sim)
                    full_route.append(to_lid)
        
        # Write route links
        for lid in full_route:
            ET.SubElement(route_links, 'link').set('refId', lid)

        departures = ET.SubElement(tr_route, 'departures')
        for tid in tids:
            dep_time = format_time(trip_starts[tid])
            veh_id = f"veh_{tid}"
            used_vehicle_ids.append((veh_id, mode))
            vehicle_counts[mode] += 1
            
            dep = ET.SubElement(departures, 'departure')
            dep.set('id', tid)
            dep.set('departureTime', dep_time)
            dep.set('vehicleRefId', veh_id)

xml_str = minidom.parseString(ET.tostring(root_sched)).toprettyxml(indent="  ")
doctype = '<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">\n'
with open(OUTPUT_SCHEDULE, 'w', encoding='utf-8') as f:
    lines = xml_str.split('\n')
    f.write(lines[0] + '\n')
    f.write(doctype)
    f.write('\n'.join(lines[1:]))

print(f"Written schedule to {OUTPUT_SCHEDULE}")

# Vehicles XML with XSD namespace
root_veh = ET.Element('vehicleDefinitions')
root_veh.set('xmlns', 'http://www.matsim.org/files/dtd')
root_veh.set('xmlns:xsi', 'http://www.w3.org/2001/XMLSchema-instance')
root_veh.set('xsi:schemaLocation', 'http://www.matsim.org/files/dtd http://www.matsim.org/files/dtd/vehicleDefinitions_v2.0.xsd')

for vtype, props in VEHICLE_TYPES.items():
    vt = ET.SubElement(root_veh, 'vehicleType')
    vt.set('id', vtype)
    # Correct schema: capacity has seats and standingRoomInPersons as attributes
    cap = ET.SubElement(vt, 'capacity')
    cap.set('seats', str(props['capacity']))
    cap.set('standingRoomInPersons', '0')
    ET.SubElement(vt, 'length').set('meter', str(props['length']))
    ET.SubElement(vt, 'width').set('meter', str(props['width']))

for veh_id, mode in used_vehicle_ids:
    v = ET.SubElement(root_veh, 'vehicle')
    v.set('id', veh_id)
    v.set('type', mode)

xml_str_v = minidom.parseString(ET.tostring(root_veh)).toprettyxml(indent="  ")
with open(OUTPUT_VEHICLES, 'w', encoding='utf-8') as f:
    f.write(xml_str_v)

print(f"Written vehicles to {OUTPUT_VEHICLES}")
