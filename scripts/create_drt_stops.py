"""
Extract DRT stops from existing transit schedule
Creates a DRT-only transit stop file for stopbased DRT operation
"""
import xml.etree.ElementTree as ET

# Load transit schedule
tree = ET.parse('input/jeonggwan-transit-schedule.xml')
root = tree.getroot()

# Get all stopFacilities
stops = root.findall('.//stopFacility')
print(f'Total bus stops in transit schedule: {len(stops)}')

# Create DRT stops XML
drt_root = ET.Element('transitSchedule')
transit_stops = ET.SubElement(drt_root, 'transitStops')

for stop in stops:
    # Copy stop to DRT stops file
    drt_stop = ET.SubElement(transit_stops, 'stopFacility')
    drt_stop.set('id', stop.get('id'))
    drt_stop.set('x', stop.get('x'))
    drt_stop.set('y', stop.get('y'))
    if stop.get('linkRefId'):
        drt_stop.set('linkRefId', stop.get('linkRefId'))
    if stop.get('name'):
        drt_stop.set('name', stop.get('name'))

# Write to file
output_file = 'input/jeonggwan-drt-stops.xml'

# Build XML string
from xml.dom import minidom
xml_str = ET.tostring(drt_root, encoding='unicode')
dom = minidom.parseString(xml_str)
pretty_xml = dom.toprettyxml(indent="  ")

# Remove extra blank lines and fix declaration
lines = [line for line in pretty_xml.split('\n') if line.strip()]
lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
lines.insert(1, '<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v1.dtd">')

with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print(f'\nDRT stops file created: {output_file}')
print(f'Total DRT stops: {len(stops)}')
