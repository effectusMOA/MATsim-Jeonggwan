"""
Compare GTFS routes with MATSim Transit Schedule routes
Identify routes that exist in GTFS but are missing in MATSim
"""
import csv
import xml.etree.ElementTree as ET
import json

# Load GTFS route IDs for Jeonggwan
print("1. Loading GTFS routes for Jeonggwan...")
with open('output/gtfs_jeonggwan_analysis.json', 'r', encoding='utf-8') as f:
    gtfs_data = json.load(f)

gtfs_routes = {r['route_id']: r['short_name'] for r in gtfs_data['routes']}
print(f"   GTFS has {len(gtfs_routes)} routes in Jeonggwan")

# Load MATSim Transit Schedule line IDs
print("\n2. Loading MATSim Transit Schedule lines...")
tree = ET.parse('input/regional-transit-schedule.xml')
root = tree.getroot()

matsim_lines = set()
for line in root.findall('.//transitLine'):
    matsim_lines.add(line.get('id'))

print(f"   MATSim has {len(matsim_lines)} total transit lines")

# Compare
print("\n3. Comparing GTFS routes with MATSim lines...")
print("="*60)

missing_in_matsim = []
found_in_matsim = []

for gtfs_route_id, short_name in gtfs_routes.items():
    # MATSim might use different ID format
    # Try various matching patterns
    found = False
    for matsim_id in matsim_lines:
        if gtfs_route_id in matsim_id or matsim_id in gtfs_route_id:
            found = True
            found_in_matsim.append({
                'gtfs_id': gtfs_route_id,
                'short_name': short_name,
                'matsim_id': matsim_id
            })
            break
    
    if not found:
        # Try matching by partial ID
        route_num = gtfs_route_id.split('_')[-1] if '_' in gtfs_route_id else gtfs_route_id
        for matsim_id in matsim_lines:
            if route_num in matsim_id:
                found = True
                found_in_matsim.append({
                    'gtfs_id': gtfs_route_id,
                    'short_name': short_name,
                    'matsim_id': matsim_id
                })
                break
    
    if not found:
        missing_in_matsim.append({
            'gtfs_id': gtfs_route_id,
            'short_name': short_name
        })

print(f"\n✅ Found in MATSim: {len(found_in_matsim)} routes")
for r in found_in_matsim[:5]:
    print(f"   {r['short_name']}: {r['gtfs_id']} -> {r['matsim_id']}")

print(f"\n❌ Missing in MATSim: {len(missing_in_matsim)} routes")
for r in missing_in_matsim:
    print(f"   {r['short_name']}: {r['gtfs_id']}")

# Save results
results = {
    'gtfs_route_count': len(gtfs_routes),
    'matsim_line_count': len(matsim_lines),
    'found_in_matsim': found_in_matsim,
    'missing_in_matsim': missing_in_matsim
}

with open('output/gtfs_matsim_comparison.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved to output/gtfs_matsim_comparison.json")
