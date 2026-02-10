"""Check why some DRT vehicles are not being used"""
import pandas as pd
import xml.etree.ElementTree as ET

# Get used vehicles from legs
legs = pd.read_csv('output/jeonggwan-drt/null-drt.output_drt_legs_drt.csv', sep=';')
used_vehicles = set(legs['vehicleId'].unique())

# Get vehicle start links
tree = ET.parse('input/jeonggwan-drt-vehicles.xml')
root = tree.getroot()
vehicles = root.findall('.//vehicle')

unused_links = []
used_links = []
all_veh_info = []

for v in vehicles:
    vid = v.get('id')
    link = v.get('startLinkId', v.get('start_link', 'unknown'))
    is_used = vid in used_vehicles
    all_veh_info.append((vid, link, is_used))
    if is_used:
        used_links.append(link)
    else:
        unused_links.append(link)

# Parse network to check modes
net_tree = ET.parse('input/jeonggwan-network-moct.xml')
net_root = net_tree.getroot()

# Build link dictionary
link_dict = {}
for l in net_root.findall('.//link'):
    link_id = l.get('id')
    link_dict[link_id] = {
        'modes': l.get('modes', 'not_specified'),
        'length': l.get('length'),
        'freespeed': l.get('freespeed'),
        'from': l.get('from'),
        'to': l.get('to')
    }

print('=== VEHICLE START LINK ANALYSIS ===')
print()
print(f"{'Vehicle':<15} {'Used':<6} {'Modes':<30} {'Length':<10}")
print('-' * 70)

for vid, link, is_used in sorted(all_veh_info):
    info = link_dict.get(link, {})
    modes = info.get('modes', 'N/A')
    length = info.get('length', 'N/A')
    used_str = 'YES' if is_used else 'NO'
    print(f"{vid:<15} {used_str:<6} {modes:<30} {length:<10}")

# Check if car mode is the issue
print()
print('=== MODE ANALYSIS ===')
unused_modes = [link_dict.get(l, {}).get('modes', 'N/A') for l in unused_links]
used_modes = [link_dict.get(l, {}).get('modes', 'N/A') for l in used_links]

print(f'Unused vehicle link modes: {set(unused_modes)}')
print(f'Used vehicle link modes: {set(used_modes)}')

# Check if 'car' is in modes
print()
print('=== CAR MODE CHECK ===')
for vid, link, is_used in all_veh_info:
    info = link_dict.get(link, {})
    modes = info.get('modes', '')
    has_car = 'car' in modes if modes else False
    if not is_used:
        print(f'{vid} (UNUSED): has_car={has_car}, modes={modes}')
