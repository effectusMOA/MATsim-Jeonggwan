import pandas as pd
import xml.etree.ElementTree as ET
from scipy.spatial import cKDTree
import numpy as np

# Configuration
NETWORK_FILE = "input/jeonggwan-network-expanded.xml"
TRANSIT_SCHEDULE_FILE = "input/jeonggwan-transit-schedule.xml"
AGENTS = [
    {
        "id": "102026569102932",
        "carAvail": "never",
        "from_x": 1153650.0, "from_y": 1704312.0, # Jeonggwan (likely)
        "to_x": 1098484.0, "to_y": 1681037.0      # Far away
    },
    {
        "id": "1001048084221573",
        "carAvail": "always",
        "from_x": 1151491.0, "from_y": 1705430.0,
        "to_x": 1165774.0, "to_y": 1791586.0
    }
]

print("Loading Transit Schedule...")
# Load stops
stops = []
tree = ET.parse(TRANSIT_SCHEDULE_FILE)
root = tree.getroot()

for stop in root.find('transitStops').findall('stopFacility'):
    stops.append({
        'id': stop.get('id'),
        'x': float(stop.get('x')),
        'y': float(stop.get('y')),
        'linkId': stop.get('linkRefId')
    })
    
df_stops = pd.DataFrame(stops)
stops_tree = cKDTree(df_stops[['x', 'y']].values)

print(f"Loaded {len(df_stops)} transit stops.")

print("\nChecking Connectivity for Agents...")

for agent in AGENTS:
    print("\n" + "="*50)
    print(f"Agent {agent['id']} ({agent['carAvail']})")
    print(f"Origin: ({agent['from_x']}, {agent['from_y']})")
    print(f"Dest:   ({agent['to_x']}, {agent['to_y']})")
    
    # Check Origin Connectivity
    dist_o, idx_o = stops_tree.query([agent['from_x'], agent['from_y']], k=3)
    print(f"\n[Origin Connectivity]")
    for d, i in zip(dist_o, idx_o):
        stop = df_stops.iloc[i]
        print(f"  - Stop {stop['id']} at {d:.1f}m")
        # Find lines serving this stop? (Too extensive to parse simplified xml structure for lines)
        # Just existence is good first check.
        
    # Check Dest Connectivity
    dist_d, idx_d = stops_tree.query([agent['to_x'], agent['to_y']], k=3)
    print(f"\n[Dest Connectivity]")
    for d, i in zip(dist_d, idx_d):
        stop = df_stops.iloc[i]
        print(f"  - Stop {stop['id']} at {d:.1f}m")
        
    # Check direct distance
    direct_dist = ((agent['from_x'] - agent['to_x'])**2 + (agent['from_y'] - agent['to_y'])**2)**0.5
    print(f"\nDirect Distance: {direct_dist/1000:.1f} km")
    
    # Basic conclusion
    if min(dist_o) > 2000 or min(dist_d) > 2000:
        print(">> CONCLUSION: Stop access/egress > 2km. Likely OUT of transit service area.")
    else:
        print(">> CONCLUSION: Stops exist within 2km. Check if lines connect or if transfer is possible.")
        # If both ends have stops, it might be a routing failure or schedule gap.
