"""
Create Regional Network V2 with OSM-MOCT Bridge Links

This script creates a merged network from:
1. OSM-based Jeonggwan network (detailed local streets)
2. MOCT standard node-link network (regional/expressway coverage)

The key improvement over v1 is that it creates bridge links to connect
the two networks, preventing OSM links from being lost during SCC cleaning.
"""

import geopandas as gpd
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from shapely.geometry import box, Point, LineString
from scipy.spatial import cKDTree
import numpy as np
import os
from pyproj import Transformer
import networkx as nx

# Configuration
JEONGGWAN_NET_FILE = "input/jeonggwan-network-cleaned.xml"
MOCT_LINK_FILE = "NODE_LINK/MOCT_LINK.shp"
MOCT_NODE_FILE = "NODE_LINK/MOCT_NODE.shp"
OUTPUT_FILE = "input/regional-network-v2.xml"

# Regional BBox (Busan, Ulsan, Yangsan approx)
REGIONAL_BBOX = box(128.8, 35.0, 129.5, 35.7)

# Jeonggwan BBox
JEONGGWAN_BBOX = box(129.13, 35.29, 129.24, 35.37)

# Bridge link parameters
BRIDGE_MAX_DISTANCE = 100  # meters - max distance to create bridge
BRIDGE_FREESPEED = 8.33    # 30 km/h
BRIDGE_CAPACITY = 1000
BRIDGE_LANES = 1

def load_matsim_network(xml_file):
    """Load MATSim network from XML file."""
    print(f"Loading existing network: {xml_file}...")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    nodes = []
    links = []
    
    for node in root.findall('.//node'):
        nodes.append({
            'id': node.get('id'),
            'x': float(node.get('x')),
            'y': float(node.get('y')),
            'source': 'osm'
        })
        
    for link in root.findall('.//link'):
        links.append({
            'id': link.get('id'),
            'from': link.get('from'),
            'to': link.get('to'),
            'length': link.get('length'),
            'freespeed': link.get('freespeed'),
            'capacity': link.get('capacity'),
            'permlanes': link.get('permlanes'),
            'modes': link.get('modes'),
            'source': 'osm'
        })
        
    return pd.DataFrame(nodes), pd.DataFrame(links)

def load_moct_network():
    """Load and convert MOCT network."""
    print("Loading Standard Node Links...")
    moct_links = gpd.read_file(MOCT_LINK_FILE, encoding='cp949')
    moct_nodes = gpd.read_file(MOCT_NODE_FILE, encoding='cp949')
    
    # Set CRS if missing
    if moct_links.crs is None:
        moct_links.set_crs(epsg=5186, inplace=True)
        moct_nodes.set_crs(epsg=5186, inplace=True)
    
    # Reproject to EPSG:5179
    moct_links = moct_links.to_crs(epsg=5179)
    moct_nodes = moct_nodes.to_crs(epsg=5179)
    
    # Define BBox in 5179
    transformer = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)
    minx, miny = transformer.transform(128.8, 35.0)
    maxx, maxy = transformer.transform(129.5, 35.7)
    regional_bbox_5179 = box(minx, miny, maxx, maxy)
    
    jg_minx, jg_miny = transformer.transform(129.13, 35.29)
    jg_maxx, jg_maxy = transformer.transform(129.24, 35.37)
    jeonggwan_bbox_5179 = box(jg_minx, jg_miny, jg_maxx, jg_maxy)
    
    # Filter spatially
    moct_links = moct_links[moct_links.geometry.within(regional_bbox_5179)]
    moct_nodes = moct_nodes[moct_nodes.geometry.within(regional_bbox_5179)]
    
    # Exclude Jeonggwan area to avoid duplicates with OSM
    moct_links = moct_links[~moct_links.geometry.within(jeonggwan_bbox_5179)]
    
    print(f"  -> MOCT (Filtered): {len(moct_nodes)} nodes, {len(moct_links)} links")
    
    # Convert to MATSim format
    CAPACITY_PER_LANE = {1: 2000, 2: 1800, 3: 1600, 4: 1400, 5: 1200, 6: 800}
    
    new_nodes = []
    for idx, row in moct_nodes.iterrows():
        nid = str(row['NODE_ID'])
        new_nodes.append({
            'id': nid,
            'x': row.geometry.x,
            'y': row.geometry.y,
            'source': 'moct'
        })
        
    new_links = []
    for idx, row in moct_links.iterrows():
        lid = str(row['LINK_ID'])
        f_node = str(row['F_NODE'])
        t_node = str(row['T_NODE'])
        
        length = row.geometry.length
        lanes = int(row['LANES']) if pd.notna(row['LANES']) else 1
        speed_kmh = float(row['MAX_SPD']) if pd.notna(row['MAX_SPD']) and float(row['MAX_SPD']) > 0 else 50.0
        freespeed = speed_kmh / 3.6
        
        rank = int(row['ROAD_RANK']) if pd.notna(row['ROAD_RANK']) else 4
        capacity = lanes * CAPACITY_PER_LANE.get(rank, 1200)
        
        new_links.append({
            'id': lid,
            'from': f_node,
            'to': t_node,
            'length': f"{length:.2f}",
            'freespeed': f"{freespeed:.2f}",
            'capacity': f"{capacity:.1f}",
            'permlanes': str(lanes),
            'modes': 'car,bus',
            'source': 'moct'
        })
    
    return pd.DataFrame(new_nodes), pd.DataFrame(new_links)

def find_boundary_nodes(nodes_df, links_df):
    """Find boundary nodes (nodes at the edge of the network)."""
    # Create graph
    G = nx.Graph()
    for _, link in links_df.iterrows():
        G.add_edge(link['from'], link['to'])
    
    # Boundary nodes are those with degree 1 or 2 (endpoints or pass-through)
    # Actually, let's look for nodes at the edge of the bounding box
    
    node_coords = {}
    for _, node in nodes_df.iterrows():
        node_coords[node['id']] = (node['x'], node['y'])
    
    # Get bounding box
    xs = [c[0] for c in node_coords.values()]
    ys = [c[1] for c in node_coords.values()]
    
    margin = 100  # meters from edge
    minx, maxx = min(xs) + margin, max(xs) - margin
    miny, maxy = min(ys) + margin, max(ys) - margin
    
    boundary_nodes = []
    for nid, (x, y) in node_coords.items():
        if x < minx or x > maxx or y < miny or y > maxy:
            boundary_nodes.append(nid)
    
    return boundary_nodes

def create_bridge_links(osm_nodes, moct_nodes):
    """Create bridge links connecting nearby OSM and MOCT nodes."""
    print("Creating bridge links...")
    
    # Get all node coordinates
    osm_coords = []
    osm_ids = []
    for _, node in osm_nodes.iterrows():
        osm_coords.append([node['x'], node['y']])
        osm_ids.append(node['id'])
    
    moct_coords = []
    moct_ids = []
    for _, node in moct_nodes.iterrows():
        moct_coords.append([node['x'], node['y']])
        moct_ids.append(node['id'])
    
    if not osm_coords or not moct_coords:
        print("  Warning: Missing nodes!")
        return []
    
    osm_coords = np.array(osm_coords)
    moct_coords = np.array(moct_coords)
    
    # Build KD-tree for MOCT nodes
    moct_tree = cKDTree(moct_coords)
    
    # Find all OSM nodes within threshold of any MOCT node
    bridge_links = []
    bridge_id_counter = 0
    connected_pairs = set()
    
    # For each OSM node, find nearest MOCT node
    distances, indices = moct_tree.query(osm_coords, k=1)
    
    for i in range(len(osm_ids)):
        if distances[i] <= BRIDGE_MAX_DISTANCE:
            osm_id = osm_ids[i]
            moct_id = moct_ids[indices[i]]
            
            # Avoid duplicate pairs
            pair_key = tuple(sorted([osm_id, moct_id]))
            if pair_key in connected_pairs:
                continue
            connected_pairs.add(pair_key)
            
            dist = distances[i]
            
            # Create bidirectional bridge
            # OSM -> MOCT
            bridge_links.append({
                'id': f'bridge_{bridge_id_counter}',
                'from': osm_id,
                'to': moct_id,
                'length': f"{max(dist, 1.0):.2f}",  # Min 1m to avoid div by zero
                'freespeed': f"{BRIDGE_FREESPEED:.2f}",
                'capacity': str(BRIDGE_CAPACITY),
                'permlanes': str(BRIDGE_LANES),
                'modes': 'car,bus',
                'source': 'bridge'
            })
            bridge_id_counter += 1
            
            # MOCT -> OSM
            bridge_links.append({
                'id': f'bridge_{bridge_id_counter}',
                'from': moct_id,
                'to': osm_id,
                'length': f"{max(dist, 1.0):.2f}",
                'freespeed': f"{BRIDGE_FREESPEED:.2f}",
                'capacity': str(BRIDGE_CAPACITY),
                'permlanes': str(BRIDGE_LANES),
                'modes': 'car,bus',
                'source': 'bridge'
            })
            bridge_id_counter += 1
    
    print(f"  -> Created {len(bridge_links)} bridge links ({len(bridge_links)//2} pairs)")
    return bridge_links

def clean_network(all_nodes, all_links):
    """Clean network using SCC, now that bridges connect the components."""
    print("Cleaning network...")
    
    G = nx.DiGraph()
    
    for _, node in all_nodes.iterrows():
        G.add_node(str(node['id']), x=node['x'], y=node['y'])
        
    for _, link in all_links.iterrows():
        G.add_edge(str(link['from']), str(link['to']), id=str(link['id']), attr=link.to_dict())
    
    # Find largest SCC
    scc = max(nx.strongly_connected_components(G), key=len)
    print(f"  -> Largest SCC: {len(scc)} nodes")
    
    G_clean = G.subgraph(scc).copy()
    
    cleaned_nodes = []
    for n, data in G_clean.nodes(data=True):
        cleaned_nodes.append({'id': n, 'x': data['x'], 'y': data['y']})
        
    cleaned_links = []
    for u, v, data in G_clean.edges(data=True):
        cleaned_links.append(data['attr'])
    
    # Count by source
    osm_count = sum(1 for l in cleaned_links if l.get('source') == 'osm')
    moct_count = sum(1 for l in cleaned_links if l.get('source') == 'moct')
    bridge_count = sum(1 for l in cleaned_links if l.get('source') == 'bridge')
    
    print(f"  -> Cleaned: {len(cleaned_nodes)} nodes, {len(cleaned_links)} links")
    print(f"     - OSM: {osm_count}, MOCT: {moct_count}, Bridge: {bridge_count}")
    
    return pd.DataFrame(cleaned_nodes), pd.DataFrame(cleaned_links)

def write_network(nodes_df, links_df, output_file):
    """Write network to MATSim XML format."""
    print(f"Writing to {output_file}...")
    
    root = ET.Element('network')
    root.set('name', 'Jeonggwan + Regional Network V2 (with bridges)')
    
    nodes_elem = ET.SubElement(root, 'nodes')
    for _, row in nodes_df.iterrows():
        n = ET.SubElement(nodes_elem, 'node')
        n.set('id', str(row['id']))
        n.set('x', f"{row['x']:.1f}")
        n.set('y', f"{row['y']:.1f}")
        
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
    # 1. Load OSM (Jeonggwan) network
    osm_nodes, osm_links = load_matsim_network(JEONGGWAN_NET_FILE)
    print(f"  -> OSM: {len(osm_nodes)} nodes, {len(osm_links)} links")
    
    # 2. Load MOCT network
    moct_nodes, moct_links = load_moct_network()
    
    # 3. Create bridge links (now uses all nodes, not just boundary)
    bridge_links = create_bridge_links(osm_nodes, moct_nodes)
    bridge_links_df = pd.DataFrame(bridge_links) if bridge_links else pd.DataFrame()
    
    # 4. Merge all
    print("Merging networks...")
    all_nodes = pd.concat([osm_nodes, moct_nodes], ignore_index=True)
    
    if not bridge_links_df.empty:
        all_links = pd.concat([osm_links, moct_links, bridge_links_df], ignore_index=True)
    else:
        all_links = pd.concat([osm_links, moct_links], ignore_index=True)
    
    all_nodes.drop_duplicates(subset=['id'], inplace=True)
    all_links.drop_duplicates(subset=['id'], inplace=True)
    
    print(f"  -> Merged: {len(all_nodes)} nodes, {len(all_links)} links")
    
    # 6. Clean network
    final_nodes, final_links = clean_network(all_nodes, all_links)
    
    # 7. Write output
    write_network(final_nodes, final_links, OUTPUT_FILE)

if __name__ == "__main__":
    main()
