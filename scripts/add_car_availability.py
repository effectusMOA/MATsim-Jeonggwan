"""
Add carAvail attribute to existing population file using ACTUAL driver's license data.
Uses '운전면허' column from 정관_test.xlsx
- 운전면허=1 -> carAvail="always"
- 운전면허=0 -> carAvail="never"
"""
import xml.etree.ElementTree as ET
import pandas as pd

INPUT_FILE = "input/jeonggwan-plans-excel.xml"
EXCEL_FILE = "정관_test.xlsx"
OUTPUT_FILE = "input/jeonggwan-plans-excel-carAvail.xml"

print("="*60)
print("Adding carAvail attribute using ACTUAL license data")
print("="*60)

# Load Excel data with driver's license info
print(f"\n1. Loading Excel data from {EXCEL_FILE}...")
df_excel = pd.read_excel(EXCEL_FILE)
df_excel['agent_ucode'] = df_excel['agent_ucode'].astype(str)

# Create lookup dictionary: agent_id -> has_license
license_lookup = dict(zip(df_excel['agent_ucode'], df_excel['운전면허']))
print(f"   Total agents in Excel: {len(license_lookup):,}")
print(f"   License=1 (has license): {sum(1 for v in license_lookup.values() if v == 1):,}")
print(f"   License=0 (no license): {sum(1 for v in license_lookup.values() if v == 0):,}")

# Load population XML
print(f"\n2. Loading {INPUT_FILE}...")
tree = ET.parse(INPUT_FILE)
root = tree.getroot()

persons = root.findall('person')
print(f"   Found {len(persons)} persons in XML")

# Create new root
new_root = ET.Element('population')

car_always = 0
car_never = 0
not_found = 0

print("\n3. Adding carAvail attributes...")

for person in persons:
    person_id = person.get('id')
    
    # Look up license status from Excel data
    has_license = license_lookup.get(person_id, None)
    
    if has_license is None:
        # Agent not found in Excel - assume no car
        car_avail = "never"
        not_found += 1
    elif has_license == 1:
        car_avail = "always"
        car_always += 1
    else:
        car_avail = "never"
        car_never += 1
    
    # Create new person element
    new_person = ET.SubElement(new_root, 'person')
    new_person.set('id', person_id)
    
    # Add attributes element for carAvail
    attributes = ET.SubElement(new_person, 'attributes')
    attr = ET.SubElement(attributes, 'attribute')
    attr.set('name', 'carAvail')
    attr.set('class', 'java.lang.String')
    attr.text = car_avail
    
    # Copy existing plans
    for plan in person.findall('plan'):
        new_person.append(plan)

print(f"\n4. Statistics:")
print(f"   carAvail='always' (has license): {car_always} ({car_always/len(persons)*100:.1f}%)")
print(f"   carAvail='never' (no license):   {car_never} ({car_never/len(persons)*100:.1f}%)")
if not_found > 0:
    print(f"   Not found in Excel (default never): {not_found}")

print(f"\n5. Writing to {OUTPUT_FILE}...")

# Convert to string
xml_str = ET.tostring(new_root, encoding='unicode')

# Write with proper header
header = '<?xml version="1.0" encoding="UTF-8"?>\n'
doctype = '<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(header)
    f.write(doctype)
    f.write(xml_str)

print("\n✅ Done! carAvail now uses ACTUAL driver's license data.")
print(f"\nOutput file: {OUTPUT_FILE}")
