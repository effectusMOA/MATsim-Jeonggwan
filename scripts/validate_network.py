import xml.etree.ElementTree as ET
import sys

NETWORK_FILE = "input/regional-network-cleaned.xml"

print(f"Validating {NETWORK_FILE}...")

try:
    context = ET.iterparse(NETWORK_FILE, events=('start', 'end'))
    
    for event, elem in context:
        if event == 'end' and elem.tag == 'node':
            # Check node attributes
            try:
                x = float(elem.get('x'))
                y = float(elem.get('y'))
            except (ValueError, TypeError):
                print(f"Invalid node coordinates: {elem.attrib}")
            elem.clear()
            
        elif event == 'end' and elem.tag == 'link':
            # Check link attributes
            try:
                length = float(elem.get('length'))
                freespeed = float(elem.get('freespeed'))
                capacity = float(elem.get('capacity'))
                permlanes = float(elem.get('permlanes'))
                
                if length <= 0:
                    print(f"Invalid length {length} for link {elem.get('id')}")
                if freespeed <= 0:
                    print(f"Invalid freespeed {freespeed} for link {elem.get('id')}")
                if capacity <= 0:
                    print(f"Invalid capacity {capacity} for link {elem.get('id')}")
                if permlanes <= 0:
                    print(f"Invalid permlanes {permlanes} for link {elem.get('id')}")
                    
            except (ValueError, TypeError) as e:
                print(f"Invalid link attributes for link {elem.get('id')}: {e}")
            elem.clear()
            
    print("Validation complete.")

except ET.ParseError as e:
    print(f"XML Parse Error: {e}")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
