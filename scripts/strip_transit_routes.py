import xml.etree.ElementTree as ET
import sys

INPUT_FILE = "input/jeonggwan-transit-schedule.xml"
OUTPUT_FILE = "input/jeonggwan-transit-schedule.xml" # Overwrite

print(f"Stripping routes from {INPUT_FILE}...")

try:
    tree = ET.parse(INPUT_FILE)
    root = tree.getroot()
    
    count = 0
    for transit_route in root.findall(".//transitRoute"):
        route_elem = transit_route.find("route")
        if route_elem is not None:
            transit_route.remove(route_elem)
            count += 1
            
    print(f"Removed {count} explicit routes.")
    
    # Register namespace to avoid ns0 prefixes
    ET.register_namespace('', "http://www.matsim.org/files/dtd/transitSchedule_v2.dtd")
    
    # Write back
    # Use minidom for pretty printing if needed, or just write
    # MATSim is fine with standard XML
    tree.write(OUTPUT_FILE, encoding="UTF-8", xml_declaration=True)
    
    # Add DOCTYPE manually since ElementTree doesn't support it well
    with open(OUTPUT_FILE, 'r+', encoding='utf-8') as f:
        content = f.read()
        f.seek(0, 0)
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<!DOCTYPE transitSchedule SYSTEM "http://www.matsim.org/files/dtd/transitSchedule_v2.dtd">\n')
        # Skip the first line of content if it's the xml declaration
        if content.startswith('<?xml'):
            f.write(content.split('\n', 1)[1])
        else:
            f.write(content)
            
    print("Done!")

except Exception as e:
    print(f"Error: {e}")
