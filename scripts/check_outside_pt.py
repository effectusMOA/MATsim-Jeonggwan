"""
Check if agents OUTSIDE Core Area are using PT
"""
import gzip
import pandas as pd
from pyproj import Transformer
import warnings
warnings.filterwarnings('ignore')

pd.set_option('display.max_columns', None)
pd.set_option('display.width', 200)

print("="*70)
print("      Core Area 외부 에이전트의 PT 사용 여부 분석")
print("="*70)

# Load trips
print("\n1. Loading trips data...")
with gzip.open("output/jeonggwan-v1-multimode/null-multimode.output_trips.csv.gz", 'rt') as f:
    trips = pd.read_csv(f, sep=';')
print(f"   Total trips: {len(trips):,}")

# Define Core Area bounds
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)
core_x_min, core_y_min = transformer.transform(128.9, 35.15)
core_x_max, core_y_max = transformer.transform(129.35, 35.45)

print(f"\n2. Core Area (EPSG:5179):")
print(f"   X: {core_x_min:.0f} ~ {core_x_max:.0f}")
print(f"   Y: {core_y_min:.0f} ~ {core_y_max:.0f}")

# Classify trip origins
def is_in_core(x, y):
    return (core_x_min <= x <= core_x_max) and (core_y_min <= y <= core_y_max)

trips['origin_in_core'] = trips.apply(lambda r: is_in_core(r['start_x'], r['start_y']), axis=1)
trips['dest_in_core'] = trips.apply(lambda r: is_in_core(r['end_x'], r['end_y']), axis=1)

# Find trips where origin OR destination is OUTSIDE core
outside_trips = trips[~trips['origin_in_core'] | ~trips['dest_in_core']]
print(f"\n3. Core Area 외부 관련 통행: {len(outside_trips):,} trips")

# Check mode distribution
print("\n4. Mode distribution for trips involving OUTSIDE Core Area:")
mode_dist = outside_trips['main_mode'].value_counts()
print(mode_dist)
print("\n   Percentages:")
print((mode_dist / len(outside_trips) * 100).round(2))

# Focus on PT users outside core
pt_outside = outside_trips[outside_trips['main_mode'] == 'pt']
print(f"\n5. PT 사용 통행 (Core Area 외부 관련): {len(pt_outside):,} trips")

if len(pt_outside) > 0:
    print("\n   Sample PT trips involving outside Core Area:")
    print(pt_outside[['person', 'start_x', 'start_y', 'end_x', 'end_y', 'traveled_distance']].head(10))
    
    # Show PT trips by trip type
    print("\n6. PT 통행의 출발/도착 위치:")
    pt_outside['trip_type'] = pt_outside.apply(
        lambda r: "Origin Outside" if not is_in_core(r['start_x'], r['start_y']) 
                  else "Destination Outside", axis=1
    )
    print(pt_outside['trip_type'].value_counts())
    
    # Check if PT stops are used
    print("\n7. PT 정류장 사용 정보:")
    pt_cols = [c for c in pt_outside.columns if 'pt' in c.lower() or 'stop' in c.lower()]
    if pt_cols:
        print(f"   PT-related columns: {pt_cols}")
        sample = pt_outside[pt_cols].head(5)
        print(sample)

print("\n" + "="*70)
print("                         분석 완료!")
print("="*70)
