"""
Analyze 기장군8 (BR_TAGO_BSB5291608000) route in detail
Check what stops it serves and why it can't connect to other routes
"""
import xml.etree.ElementTree as ET
import json

TARGET_LINE_ID = "BR_TAGO_BSB5291608000"
TARGET_STOP_ID = "BS_TAGO_BSB500600000"  # D2 stop

print("="*60)
print(f"DETAILED ANALYSIS: {TARGET_LINE_ID} (기장군8)")
print("="*60)

print("\n1. Loading MATSim Transit Schedule...")
tree = ET.parse('input/regional-transit-schedule.xml')
root = tree.getroot()

# Find the target line
target_line = None
for line in root.findall('.//transitLine'):
    if line.get('id') == TARGET_LINE_ID:
        target_line = line
        break

if not target_line:
    print(f"ERROR: Line {TARGET_LINE_ID} not found!")
    exit(1)

print(f"   Found line: {TARGET_LINE_ID}")

# Analyze routes (variants) in this line
routes = target_line.findall('transitRoute')
print(f"\n2. Route variants: {len(routes)}")

all_stops = set()
for route in routes:
    route_id = route.get('id')
    stops = [s.get('refId') for s in route.find('routeProfile').findall('stop')]
    all_stops.update(stops)
    
    # Check departures
    departures = route.find('departures')
    dep_count = len(departures.findall('departure')) if departures else 0
    
    print(f"\n   Route: {route_id}")
    print(f"   Stops: {len(stops)}")
    print(f"   Departures: {dep_count}")
    print(f"   First 5 stops: {stops[:5]}")
    print(f"   Last 5 stops: {stops[-5:]}")
    
    # Check if target stop is in this route
    if TARGET_STOP_ID in stops:
        print(f"   >>> Contains D2 stop ({TARGET_STOP_ID})")

print(f"\n3. Total unique stops served by 기장군8: {len(all_stops)}")

# Check which other lines share stops with 기장군8
print("\n4. Finding connecting lines (share at least one stop)...")

# First, build stop-to-lines mapping
stop_to_lines = {}
for line in root.findall('.//transitLine'):
    line_id = line.get('id')
    for route in line.findall('transitRoute'):
        for stop in route.find('routeProfile').findall('stop'):
            stop_id = stop.get('refId')
            if stop_id not in stop_to_lines:
                stop_to_lines[stop_id] = set()
            stop_to_lines[stop_id].add(line_id)

# Find lines that share stops with 기장군8
connecting_lines = set()
for stop in all_stops:
    if stop in stop_to_lines:
        connecting_lines.update(stop_to_lines[stop])

connecting_lines.discard(TARGET_LINE_ID)  # Remove self

print(f"   Lines sharing stops with 기장군8: {len(connecting_lines)}")
if connecting_lines:
    # Show sample
    sample = list(connecting_lines)[:10]
    print(f"   Sample: {sample}")
else:
    print("   >>> NO OTHER LINES SHARE STOPS WITH 기장군8! <<<")
    print("   This explains why transfer is impossible.")

# Save results
results = {
    'line_id': TARGET_LINE_ID,
    'route_count': len(routes),
    'total_stops': len(all_stops),
    'connecting_lines_count': len(connecting_lines),
    'sample_connecting_lines': list(connecting_lines)[:20] if connecting_lines else [],
    'all_stops': list(all_stops)
}

with open('output/gijang8_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved to output/gijang8_analysis.json")
