import xml.etree.ElementTree as ET

SCHEDULE_FILE = "input/jeonggwan-transit-schedule.xml"
TRAIN_ROUTE_KEY = "RR_ACC1_S-2-DH"

def inspect_train_route():
    print(f"Inspecting {SCHEDULE_FILE} for route {TRAIN_ROUTE_KEY}...")
    tree = ET.parse(SCHEDULE_FILE)
    root = tree.getroot()
    
    # 1. Find the TransitLine
    train_line = None
    for line in root.findall('transitLine'):
        if TRAIN_ROUTE_KEY in line.get('id'):
            train_line = line
            break
            
    if not train_line:
        print("Train line not found.")
        return

    print(f"Found Line: {train_line.get('id')} ({train_line.get('name')})")
    
    # 2. Get stops from the first route profile
    route = train_line.find('transitRoute')
    if not route:
        print("No route found in line.")
        return
        
    print(f"Route ID: {route.get('id')}")
    profile = route.find('routeProfile')
    
    stop_ids = []
    for stop in profile.findall('stop'):
        stop_ids.append(stop.get('refId'))
        
    print(f"Total Stops: {len(stop_ids)}")
    
    # 3. Get Stop Details (Name, Coord)
    stops_elem = root.find('transitStops')
    print("\n--- Stop Details ---")
    for stop_fac in stops_elem.findall('stopFacility'):
        sid = stop_fac.get('id')
        if sid in stop_ids:
            name = stop_fac.get('name')
            x = stop_fac.get('x')
            y = stop_fac.get('y')
            link = stop_fac.get('linkRefId')
            print(f"Stop: {name} ({sid})")
            print(f"  Pos: ({x}, {y})")
            print(f"  Link: {link}")

if __name__ == "__main__":
    inspect_train_route()
