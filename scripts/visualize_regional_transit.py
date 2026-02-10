import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import os

NETWORK_FILE = "input/regional-network-expanded.xml"
SCHEDULE_FILE = "input/regional-transit-schedule.xml"
OUTPUT_IMG = "input/regional_transit_map_v1.png"

def visualize():
    print("Loading Network...")
    tree = ET.parse(NETWORK_FILE)
    root = tree.getroot()
    
    nodes = {}
    for node in root.findall('.//node'):
        nodes[node.get('id')] = (float(node.get('x')), float(node.get('y')))
        
    lines = []
    # Optimization: Only plot a subset of links or all if fast enough. 
    # 100k links is manageable with LineCollection.
    for link in root.findall('.//link'):
        fid = link.get('from')
        tid = link.get('to')
        if fid in nodes and tid in nodes:
            lines.append([nodes[fid], nodes[tid]])
            
    print(f"  -> {len(lines)} links loaded.")
    
    print("Loading Transit Stops...")
    stree = ET.parse(SCHEDULE_FILE)
    sroot = stree.getroot()
    
    stops_x = []
    stops_y = []
    for stop in sroot.findall('.//stopFacility'):
        stops_x.append(float(stop.get('x')))
        stops_y.append(float(stop.get('y')))
        
    print(f"  -> {len(stops_x)} stops loaded.")
    
    print("Plotting...")
    fig, ax = plt.subplots(figsize=(12, 12))
    
    # Plot Network
    lc = LineCollection(lines, colors='lightgray', linewidths=0.5, alpha=0.7)
    ax.add_collection(lc)
    
    # Plot Stops
    ax.scatter(stops_x, stops_y, c='red', s=2, alpha=0.8, label='Transit Stops')
    
    # Set bounds
    xs = [p[0] for p in nodes.values()]
    ys = [p[1] for p in nodes.values()]
    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(min(ys), max(ys))
    
    ax.set_title("Regional Network & Transit Stops (Busan-Ulsan-Yangsan)")
    ax.set_aspect('equal')
    ax.legend()
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMG, dpi=150)
    print(f"Saved visualization to {OUTPUT_IMG}")

if __name__ == "__main__":
    visualize()
