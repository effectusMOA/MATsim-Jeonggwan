
import xml.etree.ElementTree as ET
import gzip
import numpy as np
from scipy.spatial import cKDTree

plans_file = 'output/jeonggwan-v5-multimode/ITERS/it.10/null-multimode.10.plans.xml.gz'
schedule_file = 'input/jeonggwan-transit-schedule.xml'
network_file = 'input/jeonggwan-network-expanded.xml'
target_agent = '100012024100158'

print(f"Analyzing Agent {target_agent}...")

def get_coords(link_id, root_net):
    link = root_net.find(f".//link[@id='{link_id}']")
    if link is not None:
        from_node = root_net.find(f".//node[@id='{link.get('from')}']")
        return float(from_node.get('x')), float(from_node.get('y'))
    return None

# Load Network
net_tree = ET.parse(network_file)
net_root = net_tree.getroot()

# Find Agent's Trip
origin_link = None
dest_link = None
with gzip.open(plans_file, 'rb') as f:
    context = ET.iterparse(f, events=('start', 'end'))
    in_person = False
    for event, elem in context:
        if event == 'start' and elem.tag == 'person' and elem.get('id') == target_agent:
            in_person = True
        elif event == 'end' and elem.tag == 'person':
            in_person = False
        
        if in_person and event == 'end' and elem.tag == 'leg' and elem.get('mode') == 'walk':
            dist = float(elem.find('route').get('distance'))
            if dist > 20000:
                # This is the leg. We need the activity BEFORE and AFTER.
                # Simplification: let's just get the first long leg coords.
                pass
        
        # Actually, let's just find the activity links.
        if in_person and event == 'end' and elem.tag == 'activity':
             print(f"Activity: {elem.get('type')} at Link {elem.get('link')}")
             # We assume trip from home to education based on previous logs
             if elem.get('type') == 'home': origin_link = elem.get('link')
             if elem.get('type') == 'education': dest_link = elem.get('link')
        
        if not in_person:
            elem.clear()

origin_coords = get_coords(origin_link, net_root)
dest_coords = get_coords(dest_link, net_root)

print(f"Origin ({origin_link}): {origin_coords}")
print(f"Dest ({dest_link}): {dest_coords}")

# Load PT Stops
sched_tree = ET.parse(schedule_file)
sched_root = sched_tree.getroot()
stops = []
for stop in sched_root.findall('.//stopFacility'):
    stops.append({
        'id': stop.get('id'),
        'name': stop.get('name'),
        'coords': (float(stop.get('x')), float(stop.get('y')))
    })

stop_coords = np.array([s['coords'] for s in stops])
stop_tree = cKDTree(stop_coords)

def find_nearest_stops(coords, n=3):
    dists, indices = stop_tree.query(coords, k=n)
    print(f"\nNearest stops to {coords}:")
    for d, idx in zip(dists, indices):
        s = stops[idx]
        print(f"  - {s['name']} ({s['id']}): Dist {d/1000:.2f} km")

find_nearest_stops(origin_coords)
find_nearest_stops(dest_coords)
