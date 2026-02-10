"""
Analyze if trips to/from NEW network regions are using PT

New regions added: 김해, 경주, 포항, 밀양, 창원
Original region: 정관읍/양산/부산/울산 core area

We'll check:
1. Trip O-D coordinates
2. Identify trips with O or D outside original study area
3. Check mode usage for those trips
"""
import gzip
import pandas as pd
import numpy as np

print("1. Loading trips data...")
with gzip.open("output/jeonggwan-v1-multimode/null-multimode.output_trips.csv.gz", 'rt') as f:
    trips = pd.read_csv(f, sep=';')

print(f"   Total trips: {len(trips):,}")

# Check coordinates
print("\n2. Coordinate ranges (EPSG:5179):")
print(f"   start_x: {trips['start_x'].min():.0f} ~ {trips['start_x'].max():.0f}")
print(f"   start_y: {trips['start_y'].min():.0f} ~ {trips['start_y'].max():.0f}")
print(f"   end_x: {trips['end_x'].min():.0f} ~ {trips['end_x'].max():.0f}")
print(f"   end_y: {trips['end_y'].min():.0f} ~ {trips['end_y'].max():.0f}")

# Define original study area (jeonggwan/yangsan core)
# Based on original BBox: 128.9-129.35, 35.15-35.45 in WGS84
# Converted to EPSG:5179 approximately:
# Original core area (approximate in EPSG:5179)
CORE_X_MIN = 1100000  # approx 128.9°E
CORE_X_MAX = 1145000  # approx 129.35°E  
CORE_Y_MIN = 1685000  # approx 35.15°N
CORE_Y_MAX = 1720000  # approx 35.45°N

print(f"\n3. Original Core Area (EPSG:5179):")
print(f"   X: {CORE_X_MIN} ~ {CORE_X_MAX}")
print(f"   Y: {CORE_Y_MIN} ~ {CORE_Y_MAX}")

# Classify trips by O-D location
def is_in_core(x, y):
    return (CORE_X_MIN <= x <= CORE_X_MAX) and (CORE_Y_MIN <= y <= CORE_Y_MAX)

trips['origin_in_core'] = trips.apply(lambda r: is_in_core(r['start_x'], r['start_y']), axis=1)
trips['dest_in_core'] = trips.apply(lambda r: is_in_core(r['end_x'], r['end_y']), axis=1)

# Categorize trip types
def trip_type(row):
    if row['origin_in_core'] and row['dest_in_core']:
        return "Internal (Core-Core)"
    elif row['origin_in_core'] and not row['dest_in_core']:
        return "Outbound (Core->External)"
    elif not row['origin_in_core'] and row['dest_in_core']:
        return "Inbound (External->Core)"
    else:
        return "External (External-External)"

trips['trip_type'] = trips.apply(trip_type, axis=1)

print("\n4. Trip Types Distribution:")
trip_type_dist = trips['trip_type'].value_counts()
print(trip_type_dist)

print("\n5. Mode Distribution by Trip Type:")
mode_by_type = pd.crosstab(trips['trip_type'], trips['main_mode'], normalize='index') * 100
print(mode_by_type.round(2).to_string())

# Focus on trips involving external regions
external_trips = trips[~(trips['origin_in_core'] & trips['dest_in_core'])]
print(f"\n6. Trips involving external regions: {len(external_trips):,}")
print("   Mode distribution:")
ext_modes = external_trips['main_mode'].value_counts()
print(ext_modes)
print("\n   Percentages:")
print((ext_modes / len(external_trips) * 100).round(2))

# Check if PT is used for external trips
pt_external = external_trips[external_trips['main_mode'] == 'pt']
print(f"\n7. PT trips involving external regions: {len(pt_external)}")
if len(pt_external) > 0:
    print("   Sample PT external trips (first 5):")
    print(pt_external[['person', 'start_x', 'start_y', 'end_x', 'end_y', 'traveled_distance']].head())
