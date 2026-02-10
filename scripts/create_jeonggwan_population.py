import pandas as pd
import geopandas as gpd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import random
import os
from shapely.geometry import Point

# --- Configuration ---
TRIP_FILE = "정관읍.xlsx"
OUTPUT_FILE = "input/jeonggwan-plans.xml"

# Building Shapefiles
SHP_RESIDENTIAL = "건물/GIMI9_GEOCODE_20251229_152402_층별개요_정관읍_주거용건물/층별개요_정관읍_주거용건물.shp"
SHP_FACTORY = "건물/GIMI9_GEOCODE_20251229_171949_층별개요_정관읍_비주거_공장/층별개요_정관읍_비주거_공장.shp"
SHP_NON_FACTORY = "건물/GIMI9_GEOCODE_20251229_175933_층별개요_정관읍_비주거_비공장/층별개요_정관읍_비주거_비공장.shp"
# Note: There is also "Non-Residential (All)" but we use the split versions (Factory/Non-Factory) for better precision.

# Code Mappings
MODE_MAP = {
    1: "walk",
    2: "car", 15: "car", 16: "car", # Car, Truck
    3: "ride", 14: "ride", # Passenger, Taxi
    4: "bus", 5: "bus", 6: "bus", 7: "bus", 8: "bus", 9: "bus", # All buses
    10: "pt", 11: "pt", 12: "pt", 13: "pt", # Rail
    17: "bike",
    18: "ride" # Motorcycle -> ride or car? Let's use ride for now
}

PURPOSE_MAP = {
    1: "pick_drop",
    2: "work", # Return to work
    3: "home",
    4: "work",
    5: "education",
    6: "education", # Academy
    7: "work", # Business
    8: "shopping",
    9: "leisure",
    10: "leisure", # Dining
    11: "leisure", # Visit
    12: "other"
}

JOB_CODE_FACTORY = 6 # 기능원/장치기계조작/단순노무종사자

# --- Helper Functions ---
def load_building_coords(shp_path):
    print(f"Loading buildings from {shp_path}...")
    try:
        gdf = gpd.read_file(shp_path, encoding='euc-kr')
        # Ensure CRS is EPSG:5179 (Korean Central)
        if gdf.crs is None:
            print("  Warning: CRS is missing. Assuming EPSG:5179.")
            gdf.set_crs(epsg=5179, inplace=True)
        elif gdf.crs.to_string() != "EPSG:5179":
             # Some files might be 4326 or 5174, convert if needed
             # Based on inspection, Factory was 4326, others 5179.
             print(f"  Converting CRS from {gdf.crs} to EPSG:5179...")
             gdf = gdf.to_crs(epsg=5179)
             
        # Extract centroids
        centroids = gdf.geometry.centroid
        coords = [(p.x, p.y) for p in centroids]
        print(f"  -> Loaded {len(coords)} coordinates.")
        return coords
    except Exception as e:
        print(f"  Error loading {shp_path}: {e}")
        return []

def get_random_coord(pool):
    if not pool:
        return (0, 0) # Fallback
    return random.choice(pool)

def format_time(minutes):
    # Input is minutes from midnight (e.g., 600 = 10:00)
    if pd.isna(minutes):
        return "00:00:00"
    
    h = int(minutes // 60)
    m = int(minutes % 60)
    s = 0
    
    # Handle overflow (next day)
    if h >= 24:
        h = h % 24
        
    return f"{h:02d}:{m:02d}:{s:02d}"

# --- Main Execution ---
print("1. Loading Building Data...")
coords_residential = load_building_coords(SHP_RESIDENTIAL)
coords_factory = load_building_coords(SHP_FACTORY)
coords_non_factory = load_building_coords(SHP_NON_FACTORY)

# Fallback if pools are empty
if not coords_residential: coords_residential = [(1152635, 1704812)]
if not coords_factory: coords_factory = coords_residential
if not coords_non_factory: coords_non_factory = coords_residential

print("\n2. Loading Trip Data...")
df_trips = pd.read_excel(TRIP_FILE, sheet_name='통행사슬')
print(f"  -> Loaded {len(df_trips)} trip chains.")

print("\n3. Generating Plans...")
root = ET.Element('population')
root.set('desc', 'Jeonggwan-eup Population generated from 2016 Survey')
# Note: Using v5 DTD to avoid potential issues with v6 in this MATSim version/environment
# v5 uses 'act' instead of 'activity'

person_count = 0
skipped_count = 0

for idx, row in df_trips.iterrows():
    pid = str(row['person_id'])
    job_code = row.get('직업', 99)
    
    # Determine Work Location Pool based on Job
    if job_code == JOB_CODE_FACTORY:
        work_pool = coords_factory
    else:
        work_pool = coords_non_factory
        
    # Assign Home Location (Fixed for the person)
    home_coord = get_random_coord(coords_residential)
    
    # Assign Work Location (Fixed for the person)
    work_coord = get_random_coord(work_pool)
    
    person = ET.SubElement(root, 'person')
    person.set('id', pid)
    plan = ET.SubElement(person, 'plan')
    plan.set('selected', 'yes')
    
    # Iterate through trip chain columns (up to 7 trips usually)
    # Structure: 위치1 (Start), 출발시각1, 통행목적1, 도착시각1, 위치2 (Dest/Next Start)...
    # Actually, '위치1' is usually Home. '통행목적1' is purpose of trip to '위치2'.
    # Let's look at the columns: 위치1, 출발시각1, 통행목적1, 도착시각1, 위치2...
    # This implies: Start at Loc1 -> Trip(Mode?) -> Arrive Loc2 (Purpose1)
    
    # Wait, the Excel columns are:
    # 위치1, 출발시각1, 통행목적1, 도착시각1, 위치2...
    # Usually in this data:
    # Loc1 is Origin of Trip 1.
    # Purpose1 is Destination Purpose (at Loc2).
    # Loc2 is Destination of Trip 1.
    
    # We need to reconstruct the day.
    # Start Act (at Loc1) -> Leg -> Act (at Loc2) -> Leg -> ...
    
    # Assign coordinates to logical locations
    # We don't have exact coordinates for Loc1, Loc2... so we assign based on Purpose.
    # If Purpose is Home -> use home_coord
    # If Purpose is Work -> use work_coord
    # Else -> random non-factory
    
    current_coord = None
    
    # Initial Activity (at 위치1)
    # We need to guess the initial activity type.
    # Usually it's Home. Let's check '위치1_행정동명' or assume Home if it starts early.
    # Or look at the first trip purpose. If Trip 1 is "Go to Work", then Origin was Home.
    # If Trip 1 is "Go Home", then Origin was Work/Other.
    
    first_purpose_code = row.get('통행목적1')
    first_act_type = "home" # Default start
    
    if pd.notna(first_purpose_code):
        first_purpose = PURPOSE_MAP.get(first_purpose_code, "other")
        if first_purpose == "home":
            # If first trip is TO home, we started SOMEWHERE ELSE.
            # Could be work (night shift) or other.
            # Let's assume 'other' for simplicity unless we know better.
            first_act_type = "other"
        else:
            # If trip is TO work, we started at HOME.
            first_act_type = "home"
            
    # Set initial coordinate
    if first_act_type == "home":
        current_coord = home_coord
    elif first_act_type == "work":
        current_coord = work_coord
    else:
        current_coord = get_random_coord(coords_non_factory)
        
    # Add Initial Activity
    act = ET.SubElement(plan, 'act')
    act.set('type', first_act_type)
    act.set('x', f"{current_coord[0]:.1f}")
    act.set('y', f"{current_coord[1]:.1f}")
    
    # Loop through trips
    for i in range(1, 8): # 1 to 7
        dep_time_col = f'출발시각{i}'
        purpose_col = f'통행목적{i}'
        
        if pd.isna(row.get(dep_time_col)) or pd.isna(row.get(purpose_col)):
            break
            
        dep_time = format_time(row[dep_time_col])
        purpose_code = row[purpose_col]
        purpose = PURPOSE_MAP.get(purpose_code, "other")
        
        # Determine Mode (Default to car if missing, or random for variety if desired)
        # For now, let's use a simple heuristic or random to ensure traffic.
        # If we had '수단' column we would use it.
        mode = "car" 
        
        # Set end_time for the previous activity
        # 'act' variable holds the last created activity (initial or from previous iteration)
        act.set('end_time', dep_time)
        
        # Create Leg
        leg = ET.SubElement(plan, 'leg')
        leg.set('mode', mode)
        leg.set('dep_time', dep_time)
        
        # Determine Destination Coord
        if purpose == "home":
            dest_coord = home_coord
        elif purpose == "work":
            dest_coord = work_coord
        else:
            dest_coord = get_random_coord(coords_non_factory)
            
        # Create Activity
        act = ET.SubElement(plan, 'act')
        act.set('type', purpose)
        act.set('x', f"{dest_coord[0]:.1f}")
        act.set('y', f"{dest_coord[1]:.1f}")
        
        current_coord = dest_coord
print(f"\n4. Saving {person_count} plans to {OUTPUT_FILE}...")
xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")

# Replace the default XML declaration with one including the DOCTYPE for v5
doctype = '<!DOCTYPE population SYSTEM "http://www.matsim.org/files/dtd/population_v5.dtd">\n'
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    # Write XML declaration manually if needed or let minidom do it but insert DOCTYPE
    # minidom toprettyxml includes <?xml ... ?>
    # We need to insert DOCTYPE after that.
    lines = xml_str.split('\n')
    f.write(lines[0] + '\n')
    f.write(doctype)
    f.write('\n'.join(lines[1:]))

print("Done!")
