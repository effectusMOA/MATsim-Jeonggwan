import xml.etree.ElementTree as ET
import pandas as pd
import os

SCHEDULE_FILE = "input/jeonggwan-transit-schedule.xml"

def analyze_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        print(f"Error: {SCHEDULE_FILE} not found.")
        return

    print(f"Parsing {SCHEDULE_FILE}...")
    tree = ET.parse(SCHEDULE_FILE)
    root = tree.getroot()

    lines = root.findall('transitLine')
    
    stats = {
        'City Bus (BR_ACC0/MBEE/TAGO)': {'lines': 0, 'routes': 0, 'trips': 0, 'details': []},
        'Intercity Bus (BR_ACC3)': {'lines': 0, 'routes': 0, 'trips': 0, 'details': []},
        'Train/Subway (RR/TR)': {'lines': 0, 'routes': 0, 'trips': 0, 'details': []},
        'Other': {'lines': 0, 'routes': 0, 'trips': 0, 'details': []}
    }
    
    for line in lines:
        line_id = line.get('id')
        line_name = line.get('name')
        
        routes = line.findall('transitRoute')
        num_routes = len(routes)
        
        line_trips = 0
        for route in routes:
            departures = route.find('departures')
            if departures is not None:
                line_trips += len(departures.findall('departure'))
        
        # Categorize
        if line_id.startswith('BR_ACC0') or line_id.startswith('BR_MBEE') or line_id.startswith('BR_TAGO'):
            cat = 'City Bus (BR_ACC0/MBEE/TAGO)'
        elif line_id.startswith('BR_ACC3'):
            cat = 'Intercity Bus (BR_ACC3)'
        elif line_id.startswith('RR') or line_id.startswith('TR'):
            cat = 'Train/Subway (RR/TR)'
        else:
            cat = 'Other'
            
        stats[cat]['lines'] += 1
        stats[cat]['routes'] += num_routes
        stats[cat]['trips'] += line_trips
        stats[cat]['details'].append({
            'ID': line_id,
            'Name': line_name,
            'Routes': num_routes,
            'Trips': line_trips
        })

    print("\n=== Transit Schedule Analysis ===")
    print(f"Total Lines: {len(lines)}")
    
    total_trips_all = sum(s['trips'] for s in stats.values())
    print(f"Total Trips (Vehicles): {total_trips_all}")
    
    for cat, data in stats.items():
        if data['lines'] > 0:
            print(f"\n[{cat}]")
            print(f"  Lines: {data['lines']}")
            print(f"  Routes: {data['routes']}")
            print(f"  Trips: {data['trips']}")
            
            df = pd.DataFrame(data['details'])
            pd.set_option('display.max_rows', None)
            print(df.to_string(index=False))

if __name__ == "__main__":
    analyze_schedule()
