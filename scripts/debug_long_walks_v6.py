import gzip
import xml.etree.ElementTree as ET
import pandas as pd
import glob

# Configuration
BASE_DIR = "output/jeonggwan-v6-regional-multimode"

# Find latest plans file (reusing logic from previous script)
def get_latest_plans_file(base_dir):
    plans_files = glob.glob(f"{base_dir}/ITERS/it.*/???.plans.xml.gz") + glob.glob(f"{base_dir}/ITERS/it.*/*.plans.xml.gz")
    if not plans_files:
        if glob.glob(f"{base_dir}/*.output_plans.xml.gz"):
            return glob.glob(f"{base_dir}/*.output_plans.xml.gz")[0]
        return None
    
    def extract_iter(f):
        try:
            return int(f.split('it.')[1].split('\\')[0].split('/')[0])
        except:
            return -1
    plans_files.sort(key=extract_iter)
    return plans_files[-1]

PLANS_FILE = get_latest_plans_file(BASE_DIR)
print(f"Analyzing Plans File: {PLANS_FILE}")

def get_distance(x1, y1, x2, y2):
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

long_walk_agents = []

try:
    with gzip.open(PLANS_FILE, 'rt', encoding='utf-8') as f:
        print("Parsing XML stream...")
        context = ET.iterparse(f, events=('end',))
        
        current_person_id = None
        current_person_attrs = {} # carAvail, subpop
        
        for event, elem in context:
            if elem.tag == 'person':
                current_person_id = elem.get('id')
                
                # Parse Attributes (carAvail, subpop)
                # Since 'person' end tag comes AFTER children, we can find attributes in children now?
                # No, iterparse yields 'end' when closing tag is reached.
                # Attributes are usually defined in <attributes> block.
                # Let's search inside the person element we just finished parsing.
                
                car_avail = "unknown"
                subpop = "default"
                
                # Search for attributes block
                attrs_block = elem.find('attributes')
                if attrs_block is not None:
                    for attr in attrs_block.findall('attribute'):
                        if attr.get('name') == 'carAvail':
                            car_avail = attr.text
                        elif attr.get('name') == 'subpopulation':
                            subpop = attr.text

                # Find Selected Plan
                selected_plan = elem.find("./plan[@selected='yes']")
                if selected_plan is None:
                    # Fallback: check if only one plan
                    plans = elem.findall('plan')
                    if len(plans) == 1:
                        selected_plan = plans[0]
                
                if selected_plan:
                    legs = selected_plan.findall('leg')
                    activities = selected_plan.findall('activity')
                    
                    for i, leg in enumerate(legs):
                        if leg.get('mode') == 'walk':
                            if i < len(activities) - 1:
                                act_from = activities[i]
                                act_to = activities[i+1]
                                try:
                                    x1, y1 = float(act_from.get('x')), float(act_from.get('y'))
                                    x2, y2 = float(act_to.get('x')), float(act_to.get('y'))
                                    dist = get_distance(x1, y1, x2, y2)
                                    
                                    if dist > 50000: # 50km
                                        agent_info = {
                                            'id': current_person_id,
                                            'carAvail': car_avail,
                                            'subpop': subpop,
                                            'distance': dist,
                                            'from_act': act_from.get('type'),
                                            'to_act': act_to.get('type'),
                                            'from_x': x1, 'from_y': y1,
                                            'to_x': x2, 'to_y': y2
                                        }
                                        long_walk_agents.append(agent_info)
                                        print(f"Dist: {dist/1000:.1f}km | Agent: {current_person_id} | Car: {car_avail}")
                                        
                                        if len(long_walk_agents) >= 5:
                                            # Found enough examples
                                            break
                                except:
                                    pass
                    if len(long_walk_agents) >= 5:
                        break

            if elem.tag == 'person':
                elem.clear() # Clear memory
        

    import json
    with open('output/long_walk_agents.json', 'w', encoding='utf-8') as f:
        json.dump(long_walk_agents, f, indent=2, ensure_ascii=False)
        
    print(f"\nSaved {len(long_walk_agents)} agents to output/long_walk_agents.json")

except Exception as e:
    print(f"Error: {e}")
