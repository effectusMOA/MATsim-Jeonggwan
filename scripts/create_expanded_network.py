"""
Create Expanded Network for Excel-based Population

This script creates a MATSim network covering all destinations in 정관_test.xlsx
The network extends to include Busan, Ulsan, and Yangsan regions.

Coordinate ranges from Excel:
- X: 1,088,157 ~ 1,185,106 (EPSG:5179)
- Y: 1,674,319 ~ 1,805,117 (EPSG:5179)
"""

import geopandas as gpd
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from shapely.geometry import box
import numpy as np
from pyproj import Transformer
import networkx as nx

# Configuration
MOCT_LINK_FILE = "NODE_LINK/MOCT_LINK.shp"
MOCT_NODE_FILE = "NODE_LINK/MOCT_NODE.shp"
OUTPUT_FILE = "input/jeonggwan-network-expanded.xml"

# Expanded study area to cover all Excel destinations
# Convert from EPSG:5179 to WGS84 for bbox definition
# Excel ranges: X: 1,088,157~1,185,106, Y: 1,674,319~1,805,117
# Adding 5km buffer on all sides
STUDY_BBOX_5179 = {
    'minx': 1083000,  # ~5km west of 1088157
    'miny': 1669000,  # ~5km south of 1674319
    'maxx': 1190000,  # ~5km east of 1185106
    'maxy': 1810000   # ~5km north of 1805117
}

# Road type capacity per lane (veh/hr)
CAPACITY_PER_LANE = {
    1: 2000,  # Expressway
    2: 1800,  # National road
    3: 1600,  # Regional road
    4: 1400,  # City main road
    5: 1200,  # City minor road
    6: 800,   # Local road
    7: 600,   # Other
}


def load_moct_network():
    """Load and filter MOCT network for expanded study area."""
    print("Loading MOCT Standard Node Links...")
    
    moct_links = gpd.read_file(MOCT_LINK_FILE, encoding='cp949')
    moct_nodes = gpd.read_file(MOCT_NODE_FILE, encoding='cp949')
    
    # Set CRS if missing
    if moct_links.crs is None:
        moct_links.set_crs(epsg=5186, inplace=True)
        moct_nodes.set_crs(epsg=5186, inplace=True)
    
    # Convert to EPSG:5179
    moct_links = moct_links.to_crs(epsg=5179)
    moct_nodes = moct_nodes.to_crs(epsg=5179)
    
    # Create bounding box directly in EPSG:5179
    study_bbox = box(
        STUDY_BBOX_5179['minx'],
        STUDY_BBOX_5179['miny'],
        STUDY_BBOX_5179['maxx'],
        STUDY_BBOX_5179['maxy']
    )
    
    print(f"  Study area bbox (5179): "
          f"{STUDY_BBOX_5179['minx']}, {STUDY_BBOX_5179['miny']}, "
          f"{STUDY_BBOX_5179['maxx']}, {STUDY_BBOX_5179['maxy']}")
    print(f"  Coverage: ~{(STUDY_BBOX_5179['maxx']-STUDY_BBOX_5179['minx'])/1000:.0f}km x "
          f"{(STUDY_BBOX_5179['maxy']-STUDY_BBOX_5179['miny'])/1000:.0f}km")
    
    # Filter by study area
    moct_links = moct_links[moct_links.geometry.intersects(study_bbox)]
    
    # Get node IDs used by filtered links
    used_node_ids = set(moct_links['F_NODE'].astype(str)) | set(moct_links['T_NODE'].astype(str))
    moct_nodes = moct_nodes[moct_nodes['NODE_ID'].astype(str).isin(used_node_ids)]
    
    print(f"  -> Filtered: {len(moct_nodes)} nodes, {len(moct_links)} links")
    
    return moct_nodes, moct_links


def convert_to_matsim(moct_nodes, moct_links):
    """Convert MOCT data to MATSim format."""
    print("Converting to MATSim format...")
    
    # Convert nodes
    nodes = []
    for idx, row in moct_nodes.iterrows():
        nid = str(row['NODE_ID'])
        nodes.append({
            'id': nid,
            'x': row.geometry.x,
            'y': row.geometry.y
        })
    
    # Convert links
    links = []
    for idx, row in moct_links.iterrows():
        lid = str(row['LINK_ID'])
        f_node = str(row['F_NODE'])
        t_node = str(row['T_NODE'])
        
        # Get link properties
        length = row.geometry.length
        lanes = int(row['LANES']) if pd.notna(row['LANES']) and int(row['LANES']) > 0 else 1
        
        # Speed limit (MAX_SPD is in km/h)
        speed_kmh = float(row['MAX_SPD']) if pd.notna(row['MAX_SPD']) and float(row['MAX_SPD']) > 0 else 50.0
        freespeed = speed_kmh / 3.6  # Convert to m/s
        
        # Capacity based on road rank
        rank = int(row['ROAD_RANK']) if pd.notna(row['ROAD_RANK']) else 5
        capacity = lanes * CAPACITY_PER_LANE.get(rank, 1000)
        
        # Allowed modes
        modes = 'car,bus'
        
        links.append({
            'id': lid,
            'from': f_node,
            'to': t_node,
            'length': f"{length:.2f}",
            'freespeed': f"{freespeed:.2f}",
            'capacity': f"{capacity:.1f}",
            'permlanes': str(lanes),
            'modes': modes
        })
    
    return pd.DataFrame(nodes), pd.DataFrame(links)


def clean_network(nodes_df, links_df):
    """Clean network using Strongly Connected Component analysis."""
    print("Cleaning network (SCC)...")
    
    G = nx.DiGraph()
    
    # Add nodes with coordinates
    for _, node in nodes_df.iterrows():
        G.add_node(str(node['id']), x=node['x'], y=node['y'])
    
    # Add edges
    for _, link in links_df.iterrows():
        G.add_edge(str(link['from']), str(link['to']), attr=link.to_dict())
    
    print(f"  -> Initial graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    
    # Find largest SCC
    sccs = list(nx.strongly_connected_components(G))
    largest_scc = max(sccs, key=len)
    
    print(f"  -> Found {len(sccs)} SCCs, largest has {len(largest_scc)} nodes")
    
    # Extract subgraph
    G_clean = G.subgraph(largest_scc).copy()
    
    # Convert back to DataFrames
    cleaned_nodes = []
    for n, data in G_clean.nodes(data=True):
        cleaned_nodes.append({'id': n, 'x': data['x'], 'y': data['y']})
    
    cleaned_links = []
    for u, v, data in G_clean.edges(data=True):
        cleaned_links.append(data['attr'])
    
    print(f"  -> Cleaned: {len(cleaned_nodes)} nodes, {len(cleaned_links)} links")
    
    return pd.DataFrame(cleaned_nodes), pd.DataFrame(cleaned_links)


def write_network(nodes_df, links_df, output_file):
    """Write network to MATSim XML format."""
    print(f"Writing to {output_file}...")
    
    root = ET.Element('network')
    root.set('name', 'Jeonggwan Expanded Region')
    
    # Write nodes
    nodes_elem = ET.SubElement(root, 'nodes')
    for _, row in nodes_df.iterrows():
        n = ET.SubElement(nodes_elem, 'node')
        n.set('id', str(row['id']))
        n.set('x', f"{row['x']:.1f}")
        n.set('y', f"{row['y']:.1f}")
    
    # Write links
    links_elem = ET.SubElement(root, 'links')
    for _, row in links_df.iterrows():
        l = ET.SubElement(links_elem, 'link')
        l.set('id', str(row['id']))
        l.set('from', str(row['from']))
        l.set('to', str(row['to']))
        l.set('length', str(row['length']))
        l.set('freespeed', str(row['freespeed']))
        l.set('capacity', str(row['capacity']))
        l.set('permlanes', str(row['permlanes']))
        l.set('modes', str(row['modes']))
    
    # Format XML
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    doctype = '<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n'
    
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
    
    print("Done!")


def main():
    # 1. Load MOCT data
    moct_nodes, moct_links = load_moct_network()
    
    # 2. Convert to MATSim format
    nodes_df, links_df = convert_to_matsim(moct_nodes, moct_links)
    
    # 3. Clean network (SCC)
    clean_nodes, clean_links = clean_network(nodes_df, links_df)
    
    # 4. Write output
    write_network(clean_nodes, clean_links, OUTPUT_FILE)
    
    print(f"\nNetwork summary:")
    print(f"  Nodes: {len(clean_nodes)}")
    print(f"  Links: {len(clean_links)}")
    
    # Show coordinate ranges
    print(f"\nCoordinate ranges:")
    print(f"  X: {clean_nodes['x'].min():.0f} ~ {clean_nodes['x'].max():.0f}")
    print(f"  Y: {clean_nodes['y'].min():.0f} ~ {clean_nodes['y'].max():.0f}")


if __name__ == "__main__":
    main()
