
import xml.etree.ElementTree as ET
import os

plans_file = 'input/jeonggwan-plans-v4.xml'
print(f"Analyzing {plans_file}...")

always_count = 0
never_count = 0
total_agents = 0

context = ET.iterparse(plans_file, events=('end',))

for event, elem in context:
    if elem.tag == 'person':
        total_agents += 1
        car_avail = None
        # Find attribute
        for attr in elem.findall(".//attribute"):
            if attr.get('name') == 'carAvail':
                car_avail = attr.text
                break
        
        if car_avail == 'always':
            always_count += 1
        elif car_avail == 'never':
            never_count += 1
            
        elem.clear()

print(f"Total Agents: {total_agents}")
print(f"Car Available (always): {always_count} ({always_count/total_agents*100:.2f}%)")
print(f"Car Unavailable (never): {never_count} ({never_count/total_agents*100:.2f}%)")
