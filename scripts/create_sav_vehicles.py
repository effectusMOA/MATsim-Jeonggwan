"""
Create SAV (Shared Autonomous Vehicle) vehicles for Jeonggwan scenario
Generates DVRP vehicle fleet XML file for door-to-door service
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random

# SAV Vehicle Configuration
NUM_VEHICLES = 10       # Number of SAV vehicles (fewer than DRT)
SEATS = 4               # Seats per vehicle
SERVICE_START = 6 * 3600   # 06:00 (seconds)
SERVICE_END = 22 * 3600    # 22:00 (seconds)

# Load network to get valid start links
tree = ET.parse('input/jeonggwan-network-moct.xml')
root = tree.getroot()

# Get all car-allowed links
car_links = []
for link in root.findall('.//link'):
    modes = link.get('modes', 'car')
    if 'car' in modes:
        car_links.append(link.get('id'))

print(f'Total car links: {len(car_links)}')

# Random sample for vehicle start positions (distributed)
random.seed(123)  # Different seed from DRT
start_links = random.sample(car_links, min(NUM_VEHICLES, len(car_links)))

# Create vehicles XML (DVRP format)
fleet = ET.Element('vehicles')

for i, link_id in enumerate(start_links):
    vehicle = ET.SubElement(fleet, 'vehicle')
    vehicle.set('id', f'sav_veh_{i+1}')
    vehicle.set('start_link', link_id)
    vehicle.set('t_0', str(SERVICE_START))
    vehicle.set('t_1', str(SERVICE_END))
    vehicle.set('capacity', str(SEATS))

# Write to file
output_file = 'input/jeonggwan-sav-vehicles.xml'

xml_str = ET.tostring(fleet, encoding='unicode')
dom = minidom.parseString(xml_str)
pretty_xml = dom.toprettyxml(indent="  ")

# Fix declaration
lines = [line for line in pretty_xml.split('\n') if line.strip()]
lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
lines.insert(1, '<!DOCTYPE vehicles SYSTEM "http://matsim.org/files/dtd/dvrp_vehicles_v1.dtd">')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'\nSAV vehicles file created: {output_file}')
print(f'Vehicles: {NUM_VEHICLES}, Seats: {SEATS}')
print(f'Service hours: {SERVICE_START//3600:02d}:00 - {SERVICE_END//3600:02d}:00')
print(f'Mode: door-to-door (no stops required)')
