
import xml.etree.ElementTree as ET
import gzip
import os

plans_file = 'output/jeonggwan-v5-multimode/ITERS/it.10/null-multimode.10.plans.xml.gz'
MIN_WALK_DIST = 20000 # 20km

print(f"Searching for agents with walk distance >= {MIN_WALK_DIST/1000}km in {plans_file}...")

debug_agents = []

with gzip.open(plans_file, 'rb') as f:
    context = ET.iterparse(f, events=('start', 'end'))
    current_person = None
    has_long_walk = False
    
    for event, elem in context:
        if event == 'start' and elem.tag == 'person':
            current_person = {
                'id': elem.get('id'),
                'activities': [],
                'legs': []
            }
            has_long_walk = False
        
        elif event == 'end' and elem.tag == 'activity':
            current_person['activities'].append({
                'type': elem.get('type'),
                'link': elem.get('link'),
                'end_time': elem.get('end_time')
            })
        
        elif event == 'end' and elem.tag == 'leg':
            mode = elem.get('mode')
            route = elem.find('route')
            dist = 0
            if route is not None:
                dist_str = route.get('distance')
                if dist_str:
                    dist = float(dist_str)
            
            current_person['legs'].append({
                'mode': mode,
                'dist': dist
            })
            
            if mode == 'walk' and dist >= MIN_WALK_DIST:
                has_long_walk = True
        
        elif event == 'end' and elem.tag == 'person':
            if has_long_walk:
                debug_agents.append(current_person)
            if len(debug_agents) >= 5: # Limit to 5 agents for analysis
                break
            elem.clear()

print(f"\nFound {len(debug_agents)} example agents for deep analysis:\n")

for agent in debug_agents:
    print(f"--- Agent ID: {agent['id']} ---")
    
    # Print sequence
    for i in range(len(agent['activities'])):
        act = agent['activities'][i]
        print(f"  Act: {act['type']} (Link: {act['link']}, End: {act['end_time']})")
        if i < len(agent['legs']):
            leg = agent['legs'][i]
            print(f"    >>> Leg: {leg['mode']}, Distance: {leg['dist']/1000:.2f} km")
    print()
