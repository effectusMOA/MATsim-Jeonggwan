"""
Create MATSim Plans for v4 Simulation
Input: 정관읍_합성인구_2023_ver1_260207.xlsx
Output: input/jeonggwan-plans-v4.xml

Features:
- Maps coordinates to nearest links using KDTree.
- Maps Activity Types: H->home, W->work, S->education, E->education, P->pick_drop
- Sets Person Attributes:
  - subpopulation: 'young' (Age < 65) vs 'elderly' (Age >= 65)
  - carAvail: 'always' (License == 1) vs 'never' (License == 0)
- Handles duration-based activities.
"""

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import numpy as np
from scipy.spatial import cKDTree
import os

# Configuration
EXCEL_FILE = "정관읍_합성인구_2023_ver1_260207.xlsx"
NETWORK_FILE = "input/jeonggwan-network-expanded.xml" # update if needed based on config check
OUTPUT_FILE = "input/jeonggwan-plans-v4.xml"

# Activity type mapping
ACTIVITY_MAP = {
    'H': 'home',
    'W': 'work',
    'S': 'education',
    'E': 'education', # Academy/Institute
    'P': 'pick_drop',
    'O': 'other'
}

def load_network_links():
    """Load network links for coordinate-to-link mapping."""
    print(f"Loading network links from {NETWORK_FILE}...")
    
    if not os.path.exists(NETWORK_FILE):
        raise FileNotFoundError(f"Network file not found: {NETWORK_FILE}")

    tree = ET.parse(NETWORK_FILE)
    root = tree.getroot()
    
    # Get all nodes
    nodes = {}
    for node in root.findall('.//node'):
        nodes[node.get('id')] = {
            'x': float(node.get('x')),
            'y': float(node.get('y'))
        }
    
    # Get all links with their midpoints
    links = []
    for link in root.findall('.//link'):
        from_node = nodes.get(link.get('from'))
        to_node = nodes.get(link.get('to'))
        if from_node and to_node:
            mid_x = (from_node['x'] + to_node['x']) / 2
            mid_y = (from_node['y'] + to_node['y']) / 2
            links.append({
                'id': link.get('id'),
                'x': mid_x,
                'y': mid_y
            })
    
    print(f"  Loaded {len(links)} links")
    return links

def build_link_finder(links):
    """Build KD-tree for fast nearest-link lookup."""
    print("Building spatial index...")
    coords = np.array([[l['x'], l['y']] for l in links])
    tree = cKDTree(coords)
    link_ids = [l['id'] for l in links]
    return tree, link_ids

def find_nearest_link(tree, link_ids, x, y):
    """Find the nearest link to given coordinates."""
    _, idx = tree.query([x, y])
    return link_ids[idx]

def minutes_to_time(minutes):
    """Convert minutes from midnight to HH:MM:SS format."""
    if pd.isna(minutes):
        return None
    m = int(minutes)
    hours = m // 60
    mins = m % 60
    # Handle times past midnight
    if hours >= 24:
        hours = hours % 24 # Wrap around 24h for simple display, usually MATSim handles >24h
        # meaningful for duration, but for end_time usually we want absolute time.
        # However, input seems to be within a day.
    return f"{hours:02d}:{mins:02d}:00"

def minutes_to_duration(minutes):
    """Convert duration in minutes to HH:MM:SS format."""
    if pd.isna(minutes) or minutes <= 0:
        return None
    m = int(minutes)
    hours = m // 60
    mins = m % 60
    return f"{hours:02d}:{mins:02d}:00"

def create_plans(excel_file, tree, link_ids):
    """Create plans from Excel data."""
    print(f"Loading Excel data from {excel_file}...")
    df = pd.read_excel(excel_file)
    
    print(f"  Total agents: {len(df)}")
    
    # Only process agents with trips (사슬길이 > 0)
    # Note: Column names based on inspection
    df = df[df['사슬길이'] > 0]
    print(f"  Agents with trips: {len(df)}")
    
    plans = []
    skipped = 0
    
    for idx, row in df.iterrows():
        if idx % 5000 == 0:
            print(f"  Processing agent {idx}...")
        
        agent_id = str(row['agent_ucode'])
        age = row['연령']
        license_val = row['운전면허']
        
        # Attribute Logic
        subpop = 'elderly' if age >= 65 else 'young'
        car_avail = 'always' if license_val == 1 else 'never'
        
        # Build activity sequence
        activities = []
        
        for i in range(1, 8):  # 위치1 to 위치7
            loc_col = f'위치{i}'
            x_col = f'위치{i}_X좌표'
            y_col = f'위치{i}_Y좌표'
            dep_col = f'통행{i}_출발' # This is end_time of current activity
            dur_col = f'위치{i}_체류시간' # Duration if end_time is not applicable
            
            if loc_col not in row or pd.isna(row[loc_col]):
                break
            
            loc_type = row[loc_col]
            x = row[x_col]
            y = row[y_col]
            
            if pd.isna(x) or pd.isna(y):
                break
            
            # Find nearest link
            try:
                link_id = find_nearest_link(tree, link_ids, x, y)
            except:
                skipped += 1
                break
            
            # Time Logic
            end_time = None
            duration = None
            
            if dep_col in row and pd.notna(row[dep_col]):
                end_time = minutes_to_time(row[dep_col])
            
            # Optional: Use duration if end_time is missing for intermediate acts?
            # Usually strict chains have end_time.
            # If end_time is missing AND it's not the last activity, check duration
            if not end_time and dur_col in row and pd.notna(row[dur_col]):
                duration = minutes_to_duration(row[dur_col])

            activities.append({
                'type': ACTIVITY_MAP.get(loc_type, 'other'),
                'link': link_id,
                'x': x,
                'y': y,
                'end_time': end_time,
                'duration': duration
            })
        
        # Skip if less than 2 activities
        if len(activities) < 2:
            skipped += 1
            continue
        
        # Fix last activity: no end_time, no duration usually required (open ended)
        activities[-1]['end_time'] = None 
        activities[-1]['duration'] = None
        
        plans.append({
            'id': agent_id,
            'subpopulation': subpop,
            'carAvail': car_avail,
            'activities': activities
        })
    
    print(f"  Valid plans: {len(plans)}, Skipped: {skipped}")
    return plans

def write_plans(plans, output_file):
    """Write plans to XML file."""
    print(f"Writing plans to {output_file}...")
    
    root = ET.Element('population')
    
    for plan_data in plans:
        person = ET.SubElement(root, 'person')
        person.set('id', plan_data['id'])
        
        # Attributes
        attributes = ET.SubElement(person, 'attributes')
        
        attr_subpop = ET.SubElement(attributes, 'attribute')
        attr_subpop.set('name', 'subpopulation')
        attr_subpop.set('class', 'java.lang.String')
        attr_subpop.text = plan_data['subpopulation']
        
        attr_car = ET.SubElement(attributes, 'attribute')
        attr_car.set('name', 'carAvail')
        attr_car.set('class', 'java.lang.String')
        attr_car.text = plan_data['carAvail']
        
        plan = ET.SubElement(person, 'plan')
        plan.set('selected', 'yes')
        
        activities = plan_data['activities']
        
        for i, act in enumerate(activities):
            # Act
            # Use 'activity' tag as observed in valid v6 files
            act_elem = ET.SubElement(plan, 'activity')
            act_elem.set('type', act['type'])
            act_elem.set('x', str(act['x']))
            act_elem.set('y', str(act['y']))
            act_elem.set('link', act['link'])
            
            if act['end_time']:
                 act_elem.set('end_time', act['end_time'])
            if act['duration']:
                 act_elem.set('max_dur', act['duration'])

            # Leg (except after last act)
            if i < len(activities) - 1:
                leg = ET.SubElement(plan, 'leg')
                leg.set('mode', 'car')  # Default mode

    # Write to file directly using ET
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ", level=0)
    
    with open(output_file, 'wb') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'.encode('utf-8'))
        f.write('<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'.encode('utf-8'))
        tree.write(f, encoding='utf-8', xml_declaration=False)
    
    print(f"Done! Created {len(plans)} agent plans.")

def main():
    if not os.path.exists(EXCEL_FILE):
        print(f"Error: {EXCEL_FILE} does not exist.")
        return

    # Load network and build spatial index
    links = load_network_links()
    tree, link_ids = build_link_finder(links)
    
    # Create plans from Excel
    plans = create_plans(EXCEL_FILE, tree, link_ids)
    
    # Write output
    write_plans(plans, OUTPUT_FILE)

if __name__ == "__main__":
    main()
