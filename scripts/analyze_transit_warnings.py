import re
from collections import Counter
import networkx as nx
import xml.etree.ElementTree as ET

LOG_FILE = "output/jeonggwan/logfileWarningsErrors.log"
NETWORK_FILE = "input/regional-network-cleaned.xml"

print("1. Parsing warning log...")
pattern = r"Cannot move vehicle .+ from link (\S+) to link (\S+)"

with open(LOG_FILE, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

matches = re.findall(pattern, content)
print(f"   Found {len(matches)} warnings")

# Count unique link pairs
pair_counts = Counter(matches)
print(f"   Unique link pairs: {len(pair_counts)}")

print("\n2. Top 20 problematic link pairs:")
for (from_link, to_link), count in pair_counts.most_common(20):
    print(f"   {from_link} -> {to_link}: {count} times")

# Build network graph
print("\n3. Loading network for analysis...")
tree = ET.parse(NETWORK_FILE)
root = tree.getroot()
G = nx.DiGraph()
link_info = {}

for node in root.findall('.//node'):
    G.add_node(node.get('id'))

for link in root.findall('.//link'):
    lid = link.get('id')
    from_node = link.get('from')
    to_node = link.get('to')
    length = float(link.get('length', 1000))
    link_info[lid] = {'from': from_node, 'to': to_node}
    G.add_edge(from_node, to_node, link_id=lid, weight=length)

print(f"   Graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")

# Analyze why paths fail
print("\n4. Analyzing path failures for top 10 pairs...")
categories = {
    'link_not_found': [],
    'no_path': [],
    'path_exists': []
}

for (from_link, to_link), count in pair_counts.most_common(10):
    if from_link not in link_info:
        categories['link_not_found'].append((from_link, to_link, count, f"from_link '{from_link}' not in network"))
        continue
    if to_link not in link_info:
        categories['link_not_found'].append((from_link, to_link, count, f"to_link '{to_link}' not in network"))
        continue
    
    from_end = link_info[from_link]['to']
    to_start = link_info[to_link]['from']
    
    try:
        path = nx.shortest_path(G, from_end, to_start, weight='weight')
        categories['path_exists'].append((from_link, to_link, count, len(path)))
    except nx.NetworkXNoPath:
        categories['no_path'].append((from_link, to_link, count))

print("\n5. Summary:")
print(f"   Links not found in network: {len(categories['link_not_found'])}")
for item in categories['link_not_found'][:5]:
    print(f"      - {item}")

print(f"   No path between nodes: {len(categories['no_path'])}")
for item in categories['no_path'][:5]:
    print(f"      - {item[0]} -> {item[1]} ({item[2]} times)")

print(f"   Path exists (routing issue): {len(categories['path_exists'])}")
for item in categories['path_exists'][:5]:
    print(f"      - {item[0]} -> {item[1]} ({item[2]} times, path length: {item[3]})")
