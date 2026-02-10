"""
Create MATSim Plans from 정관_test.xlsx

This script generates plans.xml from Excel travel survey data.
All trips are initially set to 'car' mode.

Excel data structure:
- 사슬타입: HWH (home-work-home), HSH (home-school-home)
- 위치1~7: Activity locations (H=Home, W=Work, S=School)
- 위치N_X좌표, 위치N_Y좌표: Coordinates in EPSG:5179
- 통행N_출발: Departure time in minutes from midnight
"""

import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import numpy as np
from scipy.spatial import cKDTree

# Configuration
EXCEL_FILE = "정관_test.xlsx"
NETWORK_FILE = "input/jeonggwan-network-expanded.xml"
OUTPUT_FILE = "input/jeonggwan-plans-excel.xml"

# Activity type mapping
ACTIVITY_MAP = {
    'H': 'home',
    'W': 'work',
    'S': 'education',
    'O': 'other'
}


def load_network_links():
    """Load network links for coordinate-to-link mapping."""
    print("Loading network links...")
    
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
        hours = hours % 24
    return f"{hours:02d}:{mins:02d}:00"


def create_plans(excel_file, tree, link_ids):
    """Create plans from Excel data."""
    print(f"Loading Excel data from {excel_file}...")
    df = pd.read_excel(excel_file)
    
    print(f"  Total agents: {len(df)}")
    print(f"  Trip chains: {df['사슬타입'].value_counts().to_dict()}")
    
    # Only process agents with trips
    df = df[df['통행여부'] == 1]
    print(f"  Agents with trips: {len(df)}")
    
    plans = []
    skipped = 0
    
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(f"  Processing agent {idx}...")
        
        agent_id = str(row['agent_ucode'])
        chain_type = row['사슬타입']
        
        # Build activity sequence
        activities = []
        
        for i in range(1, 8):  # 위치1 to 위치7
            loc_col = f'위치{i}'
            x_col = f'위치{i}_X좌표'
            y_col = f'위치{i}_Y좌표'
            dep_col = f'통행{i}_출발'
            
            if loc_col not in row or pd.isna(row[loc_col]):
                break
            
            loc_type = row[loc_col]
            x = row[x_col]
            y = row[y_col]
            
            if pd.isna(x) or pd.isna(y):
                break
            
            # Get departure time (for end_time of this activity)
            dep_time = None
            if dep_col in row:
                dep_time = minutes_to_time(row[dep_col])
            
            # Find nearest link
            try:
                link_id = find_nearest_link(tree, link_ids, x, y)
            except:
                skipped += 1
                break
            
            activities.append({
                'type': ACTIVITY_MAP.get(loc_type, 'other'),
                'link': link_id,
                'x': x,
                'y': y,
                'end_time': dep_time
            })
        
        # Skip if less than 2 activities (need at least origin and destination)
        if len(activities) < 2:
            skipped += 1
            continue
        
        # Remove end_time from last activity
        activities[-1]['end_time'] = None
        
        plans.append({
            'id': agent_id,
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
        
        plan = ET.SubElement(person, 'plan')
        plan.set('selected', 'yes')
        
        activities = plan_data['activities']
        
        for i, act in enumerate(activities):
            # Add activity
            activity = ET.SubElement(plan, 'act')
            activity.set('type', act['type'])
            # Note: removed link attribute as it's not in v5 DTD
            activity.set('x', f"{act['x']:.1f}")
            activity.set('y', f"{act['y']:.1f}")
            
            if act['end_time']:
                activity.set('end_time', act['end_time'])
            
            # Add leg after each activity except the last
            if i < len(activities) - 1:
                leg = ET.SubElement(plan, 'leg')
                leg.set('mode', 'car')  # All trips as car initially
                if act['end_time']:
                    leg.set('dep_time', act['end_time'])
    
    # Format XML
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    doctype = '<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v5.dtd">\n'
    
    # Remove minidom's XML declaration
    xml_lines = xml_str.split('\n')
    if xml_lines[0].startswith('<?xml'):
        xml_content = '\n'.join(xml_lines[1:])
    else:
        xml_content = xml_str
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(doctype)
        f.write(xml_content)
    
    print(f"Done! Created {len(plans)} agent plans.")


def main():
    # Load network and build spatial index
    links = load_network_links()
    tree, link_ids = build_link_finder(links)
    
    # Create plans from Excel
    plans = create_plans(EXCEL_FILE, tree, link_ids)
    
    # Write output
    write_plans(plans, OUTPUT_FILE)
    
    # Summary
    print("\nSummary:")
    print(f"  Total agents: {len(plans)}")
    
    # Count activity types
    activity_counts = {}
    for p in plans:
        for act in p['activities']:
            t = act['type']
            activity_counts[t] = activity_counts.get(t, 0) + 1
    print(f"  Activity counts: {activity_counts}")


if __name__ == "__main__":
    main()
