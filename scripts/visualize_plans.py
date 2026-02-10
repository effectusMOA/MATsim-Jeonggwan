import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import matplotlib.collections as mc

NETWORK_FILE = "input/jeonggwan-network.xml"
PLANS_FILE = "input/jeonggwan-plans.xml"
OUTPUT_IMAGE = "input/plans_visualization.png"

print("1. Loading Network...")
net_tree = ET.parse(NETWORK_FILE)
net_root = net_tree.getroot()

# Handle namespaces if present (MATSim XML often has them)
# But our generated network might not have complex namespaces or we can ignore them
# Let's just find 'link' and 'node'
# If namespace is present, findall needs it.
# Our generated network code: root.set('xmlns', 'http://www.matsim.org/files/dtd')
# So we need to handle it or strip it.

def strip_ns(tag):
    if '}' in tag:
        return tag.split('}', 1)[1]
    return tag

nodes = {}
links = []

for node in net_root.iter():
    tag = strip_ns(node.tag)
    if tag == 'node':
        nid = node.get('id')
        x = float(node.get('x'))
        y = float(node.get('y'))
        nodes[nid] = (x, y)
    elif tag == 'link':
        from_node = node.get('from')
        to_node = node.get('to')
        if from_node in nodes and to_node in nodes:
            links.append([nodes[from_node], nodes[to_node]])

print(f"  -> {len(links)} links loaded.")

print("2. Loading Plans...")
plans_tree = ET.parse(PLANS_FILE)
plans_root = plans_tree.getroot()

activities = {'home': [], 'work': [], 'education': [], 'shopping': [], 'leisure': [], 'other': []}

for person in plans_root.iter():
    tag = strip_ns(person.tag)
    if tag == 'act':
        act_type = person.get('type')
        x = float(person.get('x'))
        y = float(person.get('y'))
        
        if act_type in activities:
            activities[act_type].append((x, y))
        else:
            activities['other'].append((x, y))

print(f"  -> Loaded activities: { {k: len(v) for k, v in activities.items()} }")

print("3. Plotting...")
fig, ax = plt.subplots(figsize=(12, 12))

# Plot Network
lc = mc.LineCollection(links, colors='gray', linewidths=0.5, alpha=0.5, label='Network')
ax.add_collection(lc)

# Plot Activities
colors = {'home': 'blue', 'work': 'red', 'education': 'green', 'shopping': 'orange', 'leisure': 'purple', 'other': 'cyan'}
markers = {'home': '.', 'work': 'x', 'education': '^', 'shopping': '*', 'leisure': 's', 'other': 'o'}

for act_type, coords in activities.items():
    if coords:
        xs, ys = zip(*coords)
        ax.scatter(xs, ys, c=colors.get(act_type, 'black'), marker=markers.get(act_type, 'o'), 
                   s=10, alpha=0.6, label=act_type)

# Auto-scale
if nodes:
    xs = [n[0] for n in nodes.values()]
    ys = [n[1] for n in nodes.values()]
    ax.set_xlim(min(xs), max(xs))
    ax.set_ylim(min(ys), max(ys))

plt.title("Jeonggwan Population Activities & Network")
plt.xlabel("X (EPSG:5179)")
plt.ylabel("Y (EPSG:5179)")
plt.legend()
plt.grid(True, alpha=0.3)

print(f"Saving to {OUTPUT_IMAGE}...")
plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight')
print("Done!")
