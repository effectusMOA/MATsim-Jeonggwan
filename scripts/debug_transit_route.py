import xml.etree.ElementTree as ET
import sys

SCHEDULE_FILE = "input/jeonggwan-transit-schedule.xml"
NETWORK_FILE = "input/regional-network-cleaned.xml"
LINE_ID = "BR_TAGO_YSB5011008000"
NODE_FROM = "3880008705"
NODE_TO = "3880008704"

print(f"Inspecting Line {LINE_ID} in {SCHEDULE_FILE}...")

try:
    tree = ET.parse(SCHEDULE_FILE)
    root = tree.getroot()
    line = root.find(f".//transitLine[@id='{LINE_ID}']")
    
    if line is None:
        print(f"Line {LINE_ID} not found!")
    else:
        print(f"Found Line: {line.get('id')}")
        for route in line.findall('transitRoute'):
            print(f"  Route: {route.get('id')}")
            network_route = route.find('route')
            if network_route is not None:
                print("    Has explicit network route:")
                links = network_route.text.strip().split(',') if network_route.text else []
                print(f"    Link count: {len(links)}")
                # Check if problematic sequence exists
                for i in range(len(links)-1):
                    if links[i].strip() == "3880678801" and links[i+1].strip() == "3880123906":
                        print(f"    FOUND PROBLEM SEQUENCE: {links[i]} -> {links[i+1]}")
            else:
                print("    No explicit network route (implicit routing).")

except Exception as e:
    print(f"Error parsing schedule: {e}")

print(f"\nChecking connectivity between {NODE_FROM} and {NODE_TO} in {NETWORK_FILE}...")
try:
    # Simple check for any link with from=NODE_FROM and to=NODE_TO
    # Since file is large, we iterate
    found = False
    context = ET.iterparse(NETWORK_FILE, events=('end',))
    for event, elem in context:
        if elem.tag == 'link':
            if elem.get('from') == NODE_FROM and elem.get('to') == NODE_TO:
                print(f"FOUND LINK: {elem.get('id')} connects {NODE_FROM} -> {NODE_TO}")
                found = True
                break
            elem.clear()
    
    if not found:
        print(f"NO LINK found connecting {NODE_FROM} -> {NODE_TO}")

except Exception as e:
    print(f"Error parsing network: {e}")
