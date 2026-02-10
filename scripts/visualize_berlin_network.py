import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import matplotlib.collections as mc
import gzip
import random

# Berlin network file (gzipped)
NETWORK_FILE = "input/v6.4/berlin-v6.4-network-with-pt.xml.gz"
OUTPUT_IMAGE = "input/berlin_network_visualization.png"

print(f"Loading Berlin network from {NETWORK_FILE}...")

try:
    # Open gzipped file
    with gzip.open(NETWORK_FILE, 'rt', encoding='utf-8') as f:
        # Parse XML iteratively to save memory (Berlin network is huge)
        context = ET.iterparse(f, events=('end',))
        
        nodes = {}
        lines = []
        
        # Bounding box for Berlin center (approx) to zoom in, or plot all?
        # Plotting all might be too heavy. Let's try to plot a sample or the whole thing if possible.
        # Berlin coordinates are in EPSG:25833 (ETRS89 / UTM zone 33N)
        
        count = 0
        link_count = 0
        
        for event, elem in context:
            if elem.tag == 'node':
                nid = elem.get('id')
                x = float(elem.get('x'))
                y = float(elem.get('y'))
                nodes[nid] = (x, y)
                elem.clear() # Free memory
                count += 1
                
            elif elem.tag == 'link':
                from_node = elem.get('from')
                to_node = elem.get('to')
                
                if from_node in nodes and to_node in nodes:
                    # Sampling for visualization speed if too large
                    # if random.random() < 0.1: 
                    p1 = nodes[from_node]
                    p2 = nodes[to_node]
                    lines.append([p1, p2])
                    link_count += 1
                elem.clear()
                
    print(f"Loaded {len(nodes)} nodes and {link_count} links.")
    
    print("Plotting...")
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Create line collection
    # Use thinner lines and high transparency for dense networks
    lc = mc.LineCollection(lines, colors='black', linewidths=0.1, alpha=0.3)
    ax.add_collection(lc)
    
    # Auto-scale
    if nodes:
        xs = [n[0] for n in nodes.values()]
        ys = [n[1] for n in nodes.values()]
        ax.set_xlim(min(xs), max(xs))
        ax.set_ylim(min(ys), max(ys))
        ax.set_aspect('equal')
    
    plt.title(f"MATSim Berlin Network (v6.4)\nNodes: {len(nodes)}, Links: {link_count}")
    plt.xlabel("X Coordinate (EPSG:25833)")
    plt.ylabel("Y Coordinate (EPSG:25833)")
    plt.grid(True, alpha=0.3)
    
    print(f"Saving image to {OUTPUT_IMAGE}...")
    plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight')
    print("Done!")

except Exception as e:
    print(f"Error: {e}")
