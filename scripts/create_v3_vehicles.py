
import xml.etree.ElementTree as ET
from xml.dom import minidom

def create_vehicles(filename, prefix, count, capacity, start_links):
    root = ET.Element('vehicles')
    
    for i in range(1, count + 1):
        veh = ET.SubElement(root, 'vehicle')
        veh.set('id', f"{prefix}_{i}")
        # Recycle start links
        link_id = start_links[(i-1) % len(start_links)]
        veh.set('start_link', link_id)
        veh.set('t_0', "21600") # 06:00
        veh.set('t_1', "79200") # 22:00
        veh.set('capacity', str(capacity))
        
    # Format XML
    xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
    
    # Remove minidom's XML declaration if present and add correct doctype
    xml_lines = xml_str.split('\n')
    if xml_lines[0].startswith('<?xml'):
        xml_content = '\n'.join(xml_lines[1:])
    else:
        xml_content = xml_str
        
    header = '<?xml version="1.0" encoding="UTF-8"?>\n'
    doctype = '<!DOCTYPE vehicles SYSTEM "http://matsim.org/files/dtd/dvrp_vehicles_v1.dtd">\n'
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(header)
        f.write(doctype)
        f.write(xml_content)
    print(f"Created {filename} with {count} vehicles.")

# DRT Start Links (from v1)
drt_links = ["1440021003", "1440063711", "1961064501", "3880779700", "1450922701"]
create_vehicles("input/jeonggwan-drt-vehicles-v3.xml", "drt_bus", 20, 20, drt_links)

# SAV Start Links (from v1)
sav_links = ["1340307001", "1410114014", "1450734501", "3880006502", "1450422014", 
             "1440065300", "3880805900", "1380056401", "3880145208", "1380062900"]
create_vehicles("input/jeonggwan-sav-vehicles-v3.xml", "sav_veh", 30, 4, sav_links)
