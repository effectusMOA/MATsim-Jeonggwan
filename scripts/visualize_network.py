import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import matplotlib.collections as mc
import os

NETWORK_FILE = "input/jeonggwan-network.xml"
OUTPUT_IMAGE = "input/network_visualization.png"

print(f"Loading network from {NETWORK_FILE}...")

try:
    tree = ET.parse(NETWORK_FILE)
    root = tree.getroot()
    
    # Handle namespace
    ns = {'ns': 'http://www.matsim.org/files/dtd'}
    
    nodes = {}
    # Parse nodes
    # Try with namespace first, if empty try without (just in case)
    nodes_elem = root.find('ns:nodes', ns)
    if nodes_elem is None:
        nodes_elem = root.find('nodes')
        
    if nodes_elem is not None:
        for node in nodes_elem.findall('ns:node', ns) if root.find('ns:nodes', ns) else nodes_elem.findall('node'):
            nid = node.get('id')
            x = float(node.get('x'))
            y = float(node.get('y'))
            nodes[nid] = (x, y)
    else:
        print("Error: <nodes> element not found.")
        
    print(f"Loaded {len(nodes)} nodes.")
    
    lines = []
    colors = []
    
    # Parse links
    link_count = 0
    links_elem = root.find('ns:links', ns)
    if links_elem is None:
        links_elem = root.find('links')
        
    if links_elem is not None:
        for link in links_elem.findall('ns:link', ns) if root.find('ns:links', ns) else links_elem.findall('link'):
            from_node = link.get('from')
            to_node = link.get('to')
            
            if from_node in nodes and to_node in nodes:
                p1 = nodes[from_node]
                p2 = nodes[to_node]
                lines.append([p1, p2])
                link_count += 1
    else:
        print("Error: <links> element not found.")
            
    print(f"Loaded {link_count} links.")
    
    print("Plotting...")
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Create line collection for performance
    lc = mc.LineCollection(lines, colors='black', linewidths=0.5, alpha=0.6)
    ax.add_collection(lc)
    
    # Auto-scale
    xs = [n[0] for n in nodes.values()]
    ys = [n[1] for n in nodes.values()]
    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(min(ys), max(ys))
    ax.set_aspect('equal')
    
    plt.title(f"MATSim Network Visualization: Jeonggwan-eup\nNodes: {len(nodes)}, Links: {link_count}")
    plt.xlabel("X Coordinate (EPSG:5179)")
    plt.ylabel("Y Coordinate (EPSG:5179)")
    plt.grid(True, alpha=0.3)
    
    print(f"Saving image to {OUTPUT_IMAGE}...")
    plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight')
    print("Done!")
    
except Exception as e:
    print(f"Error: {e}")
