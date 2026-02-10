"""
Trace the actual transfer path from O1 to D2
Using BFS to find shortest path in terms of number of transfers
"""
import xml.etree.ElementTree as ET
from collections import defaultdict, deque
import json

# Configuration
O1_STOP = "BS_TAGO_BSB212780101"  # Origin cluster 1
D2_STOP = "BS_TAGO_BSB500600000"  # Destination cluster 2
MAX_TRANSFERS = 5  # Maximum number of transfers to search

print("="*60)
print("TRANSFER PATH TRACING: O1 -> D2")
print("="*60)
print(f"Origin: {O1_STOP}")
print(f"Destination: {D2_STOP}")

print("\n1. Loading MATSim Transit Schedule...")
tree = ET.parse('input/regional-transit-schedule.xml')
root = tree.getroot()

# Build graph: stop -> list of (next_stops_on_same_route, line_id)
# And: stop -> list of lines serving it
stop_to_lines = defaultdict(set)
line_stops = {}  # line_id -> ordered list of stops

for line in root.findall('.//transitLine'):
    line_id = line.get('id')
    for route in line.findall('transitRoute'):
        route_id = f"{line_id}_{route.get('id')}"
        stops = [s.get('refId') for s in route.find('routeProfile').findall('stop')]
        line_stops[route_id] = stops
        for stop in stops:
            stop_to_lines[stop].add(route_id)

print(f"   Built graph with {len(stop_to_lines)} stops and {len(line_stops)} routes")

# Check if O1 and D2 are in the network
print(f"\n2. Verifying stops exist in network...")
print(f"   O1 ({O1_STOP}): {len(stop_to_lines[O1_STOP])} routes")
print(f"   D2 ({D2_STOP}): {len(stop_to_lines[D2_STOP])} routes")

if not stop_to_lines[O1_STOP]:
    print("   ERROR: O1 stop has no routes!")
    exit(1)
if not stop_to_lines[D2_STOP]:
    print("   ERROR: D2 stop has no routes!")
    exit(1)

# BFS to find path with minimum transfers
print(f"\n3. Searching for path with BFS (max {MAX_TRANSFERS} transfers)...")

# State: (current_stop, current_line_or_none, num_transfers)
# We want to find path from O1 to D2
# A transfer happens when we switch lines

def find_path_bfs():
    # Each state: (stop, line, num_transfers, path)
    # path is list of (line, stop) tuples
    
    visited = set()
    queue = deque()
    
    # Start: at O1, not on any line yet
    for line in stop_to_lines[O1_STOP]:
        queue.append((O1_STOP, line, 0, [(line, O1_STOP)]))
        visited.add((O1_STOP, line))
    
    while queue:
        curr_stop, curr_line, num_transfers, path = queue.popleft()
        
        if num_transfers > MAX_TRANSFERS:
            continue
        
        # Can we reach D2 on current line?
        if curr_line in line_stops:
            stops_on_line = line_stops[curr_line]
            try:
                curr_idx = stops_on_line.index(curr_stop)
            except ValueError:
                curr_idx = -1
            
            if curr_idx >= 0:
                # Check downstream stops
                for next_stop in stops_on_line[curr_idx+1:]:
                    if next_stop == D2_STOP:
                        return num_transfers, path + [(curr_line, next_stop)]
                    
                    state = (next_stop, curr_line)
                    if state not in visited:
                        visited.add(state)
                        queue.append((next_stop, curr_line, num_transfers, 
                                     path + [(curr_line, next_stop)]))
        
        # Transfer to another line at current stop
        for other_line in stop_to_lines[curr_stop]:
            if other_line != curr_line:
                state = (curr_stop, other_line)
                if state not in visited:
                    visited.add(state)
                    queue.append((curr_stop, other_line, num_transfers + 1,
                                 path + [(f"TRANSFER->{other_line}", curr_stop)]))
    
    return -1, []  # No path found

num_transfers, path = find_path_bfs()

print("\n" + "="*60)
print("RESULT:")
print("="*60)

if num_transfers >= 0:
    print(f"✅ Path found with {num_transfers} transfers!")
    print("\nPath details:")
    for i, (line, stop) in enumerate(path):
        if "TRANSFER" in line:
            print(f"   [{i}] 🔄 TRANSFER at {stop}")
            print(f"        -> Board: {line.replace('TRANSFER->', '')}")
        else:
            print(f"   [{i}] Stop: {stop}")
            print(f"        Line: {line[:50]}...")
else:
    print(f"❌ No path found within {MAX_TRANSFERS} transfers!")
    print("   This confirms a connectivity issue in the transit network.")

# Save results
results = {
    'origin': O1_STOP,
    'destination': D2_STOP,
    'transfers_needed': num_transfers,
    'path': path if num_transfers >= 0 else None,
    'path_length': len(path) if path else 0
}

with open('output/transfer_path_o1_d2.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved to output/transfer_path_o1_d2.json")
