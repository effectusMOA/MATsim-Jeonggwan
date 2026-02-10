import geopandas as gpd
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
from shapely.geometry import box, Point, LineString
import os
from pyproj import Transformer
import networkx as nx

# Configuration
JEONGGWAN_NET_FILE = "input/jeonggwan-network-cleaned.xml"
MOCT_LINK_FILE = "NODE_LINK/MOCT_LINK.shp"
MOCT_NODE_FILE = "NODE_LINK/MOCT_NODE.shp"
OUTPUT_FILE = "input/regional-network-cleaned.xml" # Directly output cleaned file

# Regional BBox (Busan, Ulsan, Yangsan approx)
# 128.8 ~ 129.5, 35.0 ~ 35.7
REGIONAL_BBOX = box(128.8, 35.0, 129.5, 35.7)

# Jeonggwan BBox (to exclude MOCT links inside here, as we have detailed OSM)
JEONGGWAN_BBOX = box(129.13, 35.29, 129.24, 35.37)

def load_matsim_network(xml_file):
    print(f"Loading existing network: {xml_file}...")
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    nodes = []
    links = []
    
    # Handle namespaces if present
    ns = {'ns': 'http://www.matsim.org/files/dtd'}
    
    # Find nodes
    xml_nodes = root.findall('.//node')
    if not xml_nodes: xml_nodes = root.findall('.//ns:node', ns)
        
    for node in xml_nodes:
        nodes.append({
            'id': node.get('id'),
            'x': float(node.get('x')),
            'y': float(node.get('y'))
        })
        
    # Find links
    xml_links = root.findall('.//link')
    if not xml_links: xml_links = root.findall('.//ns:link', ns)
        
    for link in xml_links:
        links.append({
            'id': link.get('id'),
            'from': link.get('from'),
            'to': link.get('to'),
            'length': link.get('length'),
            'freespeed': link.get('freespeed'),
            'capacity': link.get('capacity'),
            'permlanes': link.get('permlanes'),
            'modes': link.get('modes')
        })
        
    return pd.DataFrame(nodes), pd.DataFrame(links)

def create_regional_network():
    # 1. Load Existing Jeonggwan Network
    jg_nodes_df, jg_links_df = load_matsim_network(JEONGGWAN_NET_FILE)
    print(f"  -> Jeonggwan: {len(jg_nodes_df)} nodes, {len(jg_links_df)} links")
    
    # 2. Load MOCT Data
    print("Loading Standard Node Links...")
    moct_links = gpd.read_file(MOCT_LINK_FILE, encoding='cp949')
    moct_nodes = gpd.read_file(MOCT_NODE_FILE, encoding='cp949')
    
    # 3. Filter & Reproject
    print("Filtering and Reprojecting...")
    if moct_links.crs is None:
        print("  Warning: MOCT CRS is missing. Assuming EPSG:5186.")
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
    
    # Exclude Jeonggwan area
    moct_links = moct_links[~moct_links.geometry.within(jeonggwan_bbox_5179)]
    
    print(f"  -> Regional (Filtered): {len(moct_nodes)} nodes, {len(moct_links)} links")
    
    # 4. Convert MOCT to MATSim format
    print("Converting MOCT to MATSim...")
    
    new_nodes = []
    new_links = []
    
    # MOCT Nodes
    for idx, row in moct_nodes.iterrows():
        nid = str(row['NODE_ID'])
        new_nodes.append({
            'id': nid,
            'x': row.geometry.x,
            'y': row.geometry.y
        })
        
    # MOCT Links
    CAPACITY_PER_LANE = {
        1: 2000, 2: 1800, 3: 1600, 4: 1400, 5: 1200, 6: 800
    }
    
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
            'modes': 'car,bus'
        })

    regional_nodes_df = pd.DataFrame(new_nodes)
    regional_links_df = pd.DataFrame(new_links)
    
    # 5. Merge
    print("Merging networks...")
    
    all_nodes = pd.concat([jg_nodes_df, regional_nodes_df], ignore_index=True)
    all_links = pd.concat([jg_links_df, regional_links_df], ignore_index=True)
    
    all_nodes.drop_duplicates(subset=['id'], inplace=True)
    all_links.drop_duplicates(subset=['id'], inplace=True)
    
    print(f"  -> Merged Total: {len(all_nodes)} nodes, {len(all_links)} links")
    
    # 6. Clean Network (NetworkX)
    print("Cleaning network (removing isolated components)...")
    
    G = nx.DiGraph()
    
    # Add nodes
    for _, row in all_nodes.iterrows():
        G.add_node(str(row['id']), x=row['x'], y=row['y'])
        
    # Add links
    for _, row in all_links.iterrows():
        G.add_edge(str(row['from']), str(row['to']), id=str(row['id']), attr=row.to_dict())
        
    # Find largest strongly connected component
    # Note: MATSim requires the network to be navigable. A single SCC is ideal.
    # However, if we have one-way streets entering/leaving the area, SCC might be smaller than WCC.
    # But standard node links are usually dual carriageways (represented as separate links?).
    # Let's use SCC to be safe for agents returning home.
    
    scc = max(nx.strongly_connected_components(G), key=len)
    print(f"  -> Largest SCC size: {len(scc)} nodes")
    
    G_clean = G.subgraph(scc).copy()
    
    cleaned_nodes = []
    for n, data in G_clean.nodes(data=True):
        cleaned_nodes.append({'id': n, 'x': data['x'], 'y': data['y']})
        
    cleaned_links = []
    for u, v, data in G_clean.edges(data=True):
        cleaned_links.append(data['attr'])
        
    final_nodes = pd.DataFrame(cleaned_nodes)
    final_links = pd.DataFrame(cleaned_links)
    
    print(f"  -> Cleaned Total: {len(final_nodes)} nodes, {len(final_links)} links")
    
    # 7. Write XML
    print(f"Writing to {OUTPUT_FILE}...")
    
    root = ET.Element('network')
    root.set('name', 'Jeonggwan + Regional Network (Cleaned)')
    
    nodes_elem = ET.SubElement(root, 'nodes')
    for _, row in final_nodes.iterrows():
        n = ET.SubElement(nodes_elem, 'node')
        n.set('id', str(row['id']))
        n.set('x', f"{row['x']:.1f}")
        n.set('y', f"{row['y']:.1f}")
        
    links_elem = ET.SubElement(root, 'links')
    for _, row in final_links.iterrows():
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
    
    # Remove the default XML declaration from minidom
    xml_lines = xml_str.split('\n')
    if xml_lines[0].startswith('<?xml'):
        xml_content = '\n'.join(xml_lines[1:])
    else:
        xml_content = xml_str

    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    doctype = '<!DOCTYPE network SYSTEM "http://www.matsim.org/files/dtd/network_v2.dtd">\n'
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(doctype)
        f.write(xml_content)
        
    print("Done!")

if __name__ == "__main__":
    create_regional_network()
