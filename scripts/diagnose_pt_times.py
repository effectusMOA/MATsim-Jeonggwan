"""
Diagnose PT negative travel times by examining the transit schedule
Compare with GTFS source data
"""
import xml.etree.ElementTree as ET
import csv
import os

SCHEDULE_FILE = "input/regional-transit-schedule.xml"
GTFS_DIR = "2024-TM-PT-GTFS 대중교통GTFS(2023년 기준)/202303_GTFS_DataSet"

print("="*70)
print("PT TRANSIT SCHEDULE DIAGNOSIS")
print("="*70)

# 1. Parse MATSim transit schedule
print("\n1. Parsing MATSim transit schedule...")
tree = ET.parse(SCHEDULE_FILE)
root = tree.getroot()

# Find all transitLine elements
lines = root.findall('.//transitLine')
print(f"   Total transit lines: {len(lines)}")

total_routes = 0
routes_with_negative_offset = 0
routes_with_decreasing_offset = 0
example_negative_routes = []
example_good_routes = []

for line in lines:
    line_id = line.get('id', '?')
    routes = line.findall('transitRoute')
    
    for route in routes:
        total_routes += 1
        route_id = route.get('id', '?')
        
        # Get route profile
        profile = route.find('routeProfile')
        if profile is None:
            continue
            
        stops = profile.findall('stop')
        has_negative = False
        has_decreasing = False
        prev_dep_seconds = None
        stop_data = []
        
        for stop in stops:
            ref_id = stop.get('refId')
            dep_offset = stop.get('departureOffset', '')
            arr_offset = stop.get('arrivalOffset', '')
            await_dep = stop.get('awaitDeparture', '')
            
            stop_data.append({
                'refId': ref_id,
                'arrivalOffset': arr_offset,
                'departureOffset': dep_offset,
                'awaitDeparture': await_dep
            })
            
            # Parse offset to seconds
            def parse_offset(offset_str):
                if not offset_str:
                    return None
                try:
                    parts = offset_str.split(':')
                    h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
                    return h * 3600 + m * 60 + s
                except:
                    return None
            
            dep_sec = parse_offset(dep_offset)
            arr_sec = parse_offset(arr_offset)
            
            if dep_sec is not None and dep_sec < 0:
                has_negative = True
            if arr_sec is not None and arr_sec < 0:
                has_negative = True
            
            if dep_sec is not None and prev_dep_seconds is not None:
                if dep_sec < prev_dep_seconds:
                    has_decreasing = True
            
            if dep_sec is not None:
                prev_dep_seconds = dep_sec
        
        if has_negative:
            routes_with_negative_offset += 1
            if len(example_negative_routes) < 3:
                # Get departures
                deps_elem = route.find('departures')
                deps = []
                if deps_elem is not None:
                    for dep in deps_elem.findall('departure')[:3]:
                        deps.append(dep.get('departureTime'))
                
                example_negative_routes.append({
                    'line': line_id,
                    'route': route_id,
                    'stops': stop_data,
                    'departures': deps
                })
        
        if has_decreasing:
            routes_with_decreasing_offset += 1
        
        # Collect some good routes for comparison
        if not has_negative and not has_decreasing and len(example_good_routes) < 2:
            deps_elem = route.find('departures')
            deps = []
            if deps_elem is not None:
                for dep in deps_elem.findall('departure')[:3]:
                    deps.append(dep.get('departureTime'))
            example_good_routes.append({
                'line': line_id,
                'route': route_id,
                'stops': stop_data[:8],
                'departures': deps
            })

print(f"   Total routes: {total_routes}")
print(f"   Routes with NEGATIVE offsets: {routes_with_negative_offset}")
print(f"   Routes with DECREASING offsets: {routes_with_decreasing_offset}")

# Show example negative routes
print(f"\n2. Example routes with NEGATIVE offsets:")
for i, r in enumerate(example_negative_routes):
    print(f"\n   --- Negative Route #{i+1}: {r['line']} / {r['route']} ---")
    print(f"   Departures: {r['departures']}")
    for s in r['stops'][:15]:
        print(f"     Stop {s['refId']}: arr={s['arrivalOffset']}, dep={s['departureOffset']}, await={s['awaitDeparture']}")

# Show example good routes
print(f"\n3. Example GOOD routes (for comparison):")
for i, r in enumerate(example_good_routes):
    print(f"\n   --- Good Route #{i+1}: {r['line']} / {r['route']} ---")
    print(f"   Departures: {r['departures']}")
    for s in r['stops'][:8]:
        print(f"     Stop {s['refId']}: arr={s['arrivalOffset']}, dep={s['departureOffset']}, await={s['awaitDeparture']}")

# 2. Check GTFS stop_times for the same routes
print(f"\n4. Checking GTFS source data for comparison...")

# Read first 100 lines of stop_times to understand the format
gtfs_stop_times_file = os.path.join(GTFS_DIR, "stop_times.txt")
print(f"   Reading from: {gtfs_stop_times_file}")

with open(gtfs_stop_times_file, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    headers = reader.fieldnames
    print(f"   Headers: {headers}")
    
    # Read a sample - look for the trip IDs from our negative routes
    sample_lines = []
    count = 0
    for row in reader:
        if count < 20:
            sample_lines.append(row)
        count += 1
        if count >= 20:
            break

print(f"\n   Sample GTFS stop_times (first 20 rows):")
for row in sample_lines:
    trip = row.get('trip_id', '')
    arr = row.get('arrival_time', '')
    dep = row.get('departure_time', '')
    stop = row.get('stop_id', '')
    seq = row.get('stop_sequence', '')
    print(f"     trip={trip}, arr={arr}, dep={dep}, stop={stop}, seq={seq}")

# 3. Look at routeProfile offset patterns more systematically
print(f"\n5. Offset Distribution Analysis:")

offset_values = []
for line in lines:
    for route in line.findall('transitRoute'):
        profile = route.find('routeProfile')
        if profile is None:
            continue
        for stop in profile.findall('stop'):
            dep = stop.get('departureOffset', '')
            if dep:
                try:
                    parts = dep.split(':')
                    secs = int(parts[0])*3600 + int(parts[1])*60 + int(parts[2])
                    offset_values.append(secs)
                except:
                    pass

if offset_values:
    import statistics
    neg = [v for v in offset_values if v < 0]
    pos = [v for v in offset_values if v >= 0]
    zero = [v for v in offset_values if v == 0]
    
    print(f"   Total offset values: {len(offset_values)}")
    print(f"   Negative: {len(neg)} ({len(neg)/len(offset_values)*100:.1f}%)")
    print(f"   Zero: {len(zero)} ({len(zero)/len(offset_values)*100:.1f}%)")
    print(f"   Positive: {len(pos)-len(zero)} ({(len(pos)-len(zero))/len(offset_values)*100:.1f}%)")
    
    if neg:
        print(f"   Min negative: {min(neg)/3600:.2f} hours")
        print(f"   Max negative: {max(neg)/3600:.2f} hours")
    
    if pos:
        print(f"   Max positive: {max(pos)/3600:.2f} hours")
    
    # Distribution of first-stop offsets vs last-stop offsets
    print(f"\n   Checking offset progression per route:")
    sample_progressions = 0
    for line in lines:
        for route in line.findall('transitRoute')[:3]:
            profile = route.find('routeProfile')
            if profile is None:
                continue
            stops = profile.findall('stop')
            if len(stops) < 3:
                continue
            
            first_dep = stops[0].get('departureOffset', '')
            last_arr = stops[-1].get('arrivalOffset', '')
            print(f"     {route.get('id','?')}: first_dep={first_dep}, last_arr={last_arr}, total_stops={len(stops)}")
            sample_progressions += 1
            if sample_progressions >= 10:
                break
        if sample_progressions >= 10:
            break

print("\nDone!")
