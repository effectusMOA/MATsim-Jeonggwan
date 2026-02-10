
import xml.etree.ElementTree as ET

network_file = 'input/jeonggwan-network-expanded.xml'
target_links = ['1451184101', '1360028200', '1451186301', '1930004600']

tree = ET.parse(network_file)
root = tree.getroot()

nodes = {}
for node in root.findall('.//node'):
    nodes[node.get('id')] = (node.get('x'), node.get('y'))

print(f"Coordinates for target links:")
for link in root.findall('.//link'):
    l_id = link.get('id')
    if l_id in target_links:
        f_node = link.get('from')
        coords = nodes.get(f_node)
        print(f"Link {l_id}: {coords}")
