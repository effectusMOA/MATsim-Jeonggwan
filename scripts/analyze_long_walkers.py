"""
Analyze 10km+ walk agents from baseline simulation output
Identify WHY they choose walk instead of PT

Analyzes:
1. Which agents walk 10km+
2. Their O-D coordinates 
3. Nearest PT stops to their O/D
4. Whether PT routes exist for their trips
5. Agent subpopulation and car availability
"""
import gzip
import xml.etree.ElementTree as ET
import json
import math
from collections import defaultdict, Counter

# Configuration
PLANS_FILE = "output/jeonggwan-v6-v6-baseline/ITERS/it.90/90.plans.xml.gz"
TRANSIT_SCHEDULE = "input/regional-transit-schedule.xml"
MIN_WALK_DIST = 10000  # 10km in meters
SAMPLE_SIZE = 20  # Number of agents to analyze in detail

print("="*60)
print("LONG DISTANCE WALK AGENT ANALYSIS (Baseline v6)")
print("="*60)

# 1. Parse plans and find long-distance walkers
print("\n1. Loading plans from compressed file...")
long_walk_agents = []
all_walk_distances = []
total_agents = 0
mode_counts = Counter()

with gzip.open(PLANS_FILE, 'rb') as f:
    context = ET.iterparse(f, events=['start', 'end'])
    current_person = None
    current_plan_selected = False
    current_activities = []
    current_legs = []
    person_attrs = {}
    
    for event, elem in context:
        if event == 'start' and elem.tag == 'person':
            current_person = elem.get('id')
            total_agents += 1
            current_activities = []
            current_legs = []
            person_attrs = {}
            
        elif event == 'start' and elem.tag == 'plan':
            current_plan_selected = elem.get('selected') == 'yes'
            current_activities = []
            current_legs = []
            
        elif event == 'start' and elem.tag == 'activity' and current_plan_selected:
            act_type = elem.get('type')
            x = elem.get('x')
            y = elem.get('y')
            if x and y:
                current_activities.append({
                    'type': act_type,
                    'x': float(x),
                    'y': float(y)
                })
                
        elif event == 'start' and elem.tag == 'leg' and current_plan_selected:
            mode = elem.get('mode')
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            
            # Get route distance if available
            current_legs.append({
                'mode': mode,
                'dep_time': elem.get('dep_time'),
                'trav_time': elem.get('trav_time')
            })
            
        elif event == 'start' and elem.tag == 'attributes' and current_person:
            pass
            
        elif event == 'start' and elem.tag == 'attribute' and current_person:
            attr_name = elem.get('name')
            attr_value = elem.text if elem.text else ''
            person_attrs[attr_name] = attr_value
            
        elif event == 'end' and elem.tag == 'plan' and current_plan_selected:
            # Check for long walks
            for i, leg in enumerate(current_legs):
                if leg['mode'] == 'walk' and i < len(current_activities) - 1:
                    # Calculate walk distance from activity coordinates
                    origin = current_activities[i] if i < len(current_activities) else None
                    dest = current_activities[i+1] if i+1 < len(current_activities) else None
                    
                    if origin and dest:
                        dx = origin['x'] - dest['x']
                        dy = origin['y'] - dest['y']
                        dist = math.sqrt(dx*dx + dy*dy)
                        all_walk_distances.append(dist)
                        
                        if dist >= MIN_WALK_DIST:
                            long_walk_agents.append({
                                'person_id': current_person,
                                'walk_distance_m': round(dist),
                                'origin_type': origin['type'],
                                'origin_x': origin['x'],
                                'origin_y': origin['y'],
                                'dest_type': dest['type'],
                                'dest_x': dest['x'],
                                'dest_y': dest['y'],
                                'dep_time': leg['dep_time'],
                                'subpopulation': person_attrs.get('subpopulation', 'unknown'),
                                'carAvail': person_attrs.get('carAvail', 'unknown')
                            })
            
        elif event == 'end' and elem.tag == 'person':
            current_person = None
            elem.clear()
    
print(f"   Total agents: {total_agents}")
print(f"   Total walk legs: {len(all_walk_distances)}")
print(f"   Walk legs >= 10km: {len(long_walk_agents)}")

# 2. Walk distance distribution
print(f"\n2. Walk Distance Distribution:")
dist_bins = [0, 1000, 3000, 5000, 10000, 20000, 50000, float('inf')]
dist_labels = ['0-1km', '1-3km', '3-5km', '5-10km', '10-20km', '20-50km', '50km+']
for i in range(len(dist_bins)-1):
    count = sum(1 for d in all_walk_distances if dist_bins[i] <= d < dist_bins[i+1])
    pct = count / len(all_walk_distances) * 100 if all_walk_distances else 0
    print(f"   {dist_labels[i]}: {count} ({pct:.1f}%)")

# 3. Subpopulation breakdown for long walkers
print(f"\n3. Long Walker Subpopulation:")
subpop_counts = Counter(a['subpopulation'] for a in long_walk_agents)
for subpop, count in subpop_counts.most_common():
    print(f"   {subpop}: {count}")

# 4. Car availability for long walkers
print(f"\n4. Car Availability for Long Walkers:")
car_counts = Counter(a['carAvail'] for a in long_walk_agents)
for avail, count in car_counts.most_common():
    print(f"   {avail}: {count}")

# 5. Sample detailed analysis
print(f"\n5. Sample Long Walk Agents (top {SAMPLE_SIZE}):")
long_walk_agents.sort(key=lambda x: x['walk_distance_m'], reverse=True)
sample = long_walk_agents[:SAMPLE_SIZE]

for i, agent in enumerate(sample):
    print(f"\n   Agent #{i+1}: {agent['person_id']}")
    print(f"   Distance: {agent['walk_distance_m']/1000:.1f} km")
    print(f"   {agent['origin_type']} ({agent['origin_x']:.0f}, {agent['origin_y']:.0f})")
    print(f"   → {agent['dest_type']} ({agent['dest_x']:.0f}, {agent['dest_y']:.0f})")
    print(f"   Subpop: {agent['subpopulation']}, Car: {agent['carAvail']}")
    print(f"   Departure: {agent['dep_time']}")

# 6. Mode counts
print(f"\n6. Mode Counts (all legs):")
for mode, count in mode_counts.most_common():
    print(f"   {mode}: {count}")

# Save results
results = {
    'total_agents': total_agents,
    'total_walk_legs': len(all_walk_distances),
    'long_walk_count': len(long_walk_agents),
    'subpop_breakdown': dict(subpop_counts),
    'car_avail_breakdown': dict(car_counts),
    'sample_agents': sample[:SAMPLE_SIZE],
    'mode_counts': dict(mode_counts),
    'walk_distance_distribution': {
        dist_labels[i]: sum(1 for d in all_walk_distances if dist_bins[i] <= d < dist_bins[i+1])
        for i in range(len(dist_bins)-1)
    }
}

with open('output/baseline_long_walk_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved to output/baseline_long_walk_analysis.json")
