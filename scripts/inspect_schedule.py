import xml.etree.ElementTree as ET

tree = ET.parse('input/jeonggwan-transit-schedule.xml')
root = tree.getroot()

# Find a problematic route (BSB5200105000 which goes from 1451112001 to 1451186901)
line = root.find(".//transitLine[@id='BR_TAGO_BSB5200105000']")
if line is not None:
    print(f'Found line: {line.get("id")}')
    for route in line.findall('transitRoute'):
        print(f'  Route: {route.get("id")}')
        route_elem = route.find('route')
        if route_elem is not None:
            links = [l.get('refId') for l in route_elem.findall('link')]
            print(f'    Links count: {len(links)}')
            print(f'    First 10 links: {links[:10]}')
            print(f'    Last 10 links: {links[-10:]}')
            
            # Check for problematic adjacencies
            problems = []
            for i in range(len(links)-1):
                if links[i] == '1451112001' and links[i+1] == '1451186901':
                    problems.append(i)
            
            if problems:
                print(f'    PROBLEM: 1451112001 directly followed by 1451186901 at indices: {problems}')
            else:
                print(f'    No direct 1451112001->1451186901 adjacency found!')
        else:
            print('    No <route> element found!')
        break
else:
    print('Line BR_TAGO_BSB5200105000 not found')
    
    # List available lines
    print("Available lines:")
    for line in root.findall('.//transitLine')[:5]:
        print(f"  - {line.get('id')}")
