"""
Add subpopulation and age attributes to population file based on age group.

Age Groups:
- youth: 5-19세 (면허 없음, PT/DRT 의존)
- young: 20-34세 (신기술 수용도 높음)
- middle: 35-64세 (자가용 선호, 시간 가치 높음)
- elderly: 65세+ (신기술 저항, 도보 어려움)
"""
import xml.etree.ElementTree as ET
import pandas as pd

INPUT_FILE = "input/jeonggwan-plans-excel-carAvail.xml"
EXCEL_FILE = "정관_test.xlsx"
OUTPUT_FILE = "input/jeonggwan-plans-excel-subpop.xml"

print("="*60)
print("Adding subpopulation attributes based on age")
print("="*60)

# Load Excel data with age info
print(f"\n1. Loading Excel data from {EXCEL_FILE}...")
df_excel = pd.read_excel(EXCEL_FILE)
df_excel['agent_ucode'] = df_excel['agent_ucode'].astype(str)

# Function to determine subpopulation based on age range
def get_subpopulation(age_range):
    """Map age range to subpopulation.
    
    Groups:
    - default: youth (5-19) + middle (35-64) - no special adjustments
    - young: 20-34 - tech savvy, prefers SAV/DRT
    - elderly: 65+ - tech barrier, prefers PT
    """
    if pd.isna(age_range):
        return "default"  # default
    
    age_str = str(age_range)
    
    # Extract first number from age range (e.g., "35-39세" -> 35)
    import re
    match = re.search(r'(\d+)', age_str)
    if not match:
        return "default"
    
    min_age = int(match.group(1))
    
    if min_age < 20:
        return "default"  # youth -> default (no special adjustments)
    elif min_age < 35:
        return "young"
    elif min_age < 65:
        return "default"  # middle -> default (base parameters)
    else:
        return "elderly"

# Create lookup dictionary: agent_id -> subpopulation
df_excel['subpopulation'] = df_excel['연령대'].apply(get_subpopulation)
subpop_lookup = dict(zip(df_excel['agent_ucode'], df_excel['subpopulation']))
age_lookup = dict(zip(df_excel['agent_ucode'], df_excel['연령대']))

# Count subpopulations
print(f"\n2. Subpopulation distribution:")
subpop_counts = df_excel['subpopulation'].value_counts()
for subpop, count in subpop_counts.items():
    pct = count / len(df_excel) * 100
    print(f"   {subpop}: {count:,} ({pct:.1f}%)")

# Load population XML
print(f"\n3. Loading {INPUT_FILE}...")
tree = ET.parse(INPUT_FILE)
root = tree.getroot()

persons = root.findall('person')
print(f"   Found {len(persons)} persons")

# Create new root
new_root = ET.Element('population')

youth_count = 0
young_count = 0
middle_count = 0
elderly_count = 0

print("\n4. Adding subpopulation attributes...")

for person in persons:
    person_id = person.get('id')
    
    # Get subpopulation and age
    subpop = subpop_lookup.get(person_id, "middle")
    age_range = age_lookup.get(person_id, "unknown")
    
    if subpop == "youth":
        youth_count += 1
    elif subpop == "young":
        young_count += 1
    elif subpop == "middle":
        middle_count += 1
    else:
        elderly_count += 1
    
    # Create new person element
    new_person = ET.SubElement(new_root, 'person')
    new_person.set('id', person_id)
    
    # Find existing attributes element or create new one
    old_attrs = person.find('attributes')
    new_attrs = ET.SubElement(new_person, 'attributes')
    
    # Copy existing attributes (carAvail)
    if old_attrs is not None:
        for attr in old_attrs.findall('attribute'):
            new_attr = ET.SubElement(new_attrs, 'attribute')
            new_attr.set('name', attr.get('name'))
            new_attr.set('class', attr.get('class'))
            new_attr.text = attr.text
    
    # Add subpopulation attribute
    # "default" for youth/middle
    # "young" for 20-34
    # "elderly" for 65+
    subpop_attr = ET.SubElement(new_attrs, 'attribute')
    subpop_attr.set('name', 'subpopulation')
    subpop_attr.set('class', 'java.lang.String')
    subpop_attr.text = subpop
    
    # Add age attribute
    age_attr = ET.SubElement(new_attrs, 'attribute')
    age_attr.set('name', 'age')
    age_attr.set('class', 'java.lang.String')
    age_attr.text = str(age_range)
    
    # Copy existing plans and convert 'act' to 'activity' for v6 compatibility
    # Also enforce mode based on car availability
    car_avail = "always"
    if old_attrs is not None:
        for attr in old_attrs.findall('attribute'):
            if attr.get('name') == 'carAvail':
                car_avail = attr.text
                break
    
    for plan in person.findall('plan'):
        for child in plan.iter():
            if child.tag == 'act':
                child.tag = 'activity'
            elif child.tag == 'leg':
                # Force PT mode if car is not available
                if car_avail == "never" and child.get('mode') == 'car':
                    child.set('mode', 'pt')
                    
        new_person.append(plan)

    # Statistics collection
    if subpop == "youth":
        youth_count += 1
    elif subpop == "young":
        young_count += 1
    elif subpop == "middle":
        middle_count += 1
    else:
        elderly_count += 1

print(f"\n5. Final Statistics:")
print(f"   youth (5-19):    {youth_count:,} ({youth_count/len(persons)*100:.1f}%)")
print(f"   young (20-34):   {young_count:,} ({young_count/len(persons)*100:.1f}%)")
print(f"   middle (35-64):  {middle_count:,} ({middle_count/len(persons)*100:.1f}%)")
print(f"   elderly (65+):   {elderly_count:,} ({elderly_count/len(persons)*100:.1f}%)")

print(f"\n6. Writing to {OUTPUT_FILE}...")

# Convert to string
xml_str = ET.tostring(new_root, encoding='unicode')

# Write with proper header
header = '<?xml version="1.0" encoding="UTF-8"?>\n'
doctype = '<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v6.dtd">\n'

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(header)
    f.write(doctype)
    f.write(xml_str)

print("\n✅ Done! Population now has subpopulation attributes.")
print(f"\nOutput file: {OUTPUT_FILE}")
