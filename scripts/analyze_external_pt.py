"""
Analyze PT usage for external (long-distance) trips
"""
import gzip
import pandas as pd
import numpy as np

# Load trips data
print("1. Loading trips data...")
with gzip.open("output/jeonggwan-v1-multimode/null-multimode.output_trips.csv.gz", 'rt') as f:
    trips = pd.read_csv(f, sep=';')

print(f"   Total trips: {len(trips):,}")
print(f"   Columns: {list(trips.columns)}")

# Analyze by distance
print("\n2. Mode distribution by distance category:")
trips['distance_km'] = trips['traveled_distance'] / 1000

# Define distance categories
def categorize_distance(d):
    if d < 5:
        return "1. Local (<5km)"
    elif d < 15:
        return "2. Short (5-15km)"
    elif d < 30:
        return "3. Medium (15-30km)"
    else:
        return "4. Long (>30km, External)"

trips['distance_cat'] = trips['distance_km'].apply(categorize_distance)

# Cross-tabulation
print("\nTrip counts by distance category and mode:")
mode_by_dist = pd.crosstab(trips['distance_cat'], trips['main_mode'])
print(mode_by_dist)

print("\nPercentage by distance category:")
mode_by_dist_pct = pd.crosstab(trips['distance_cat'], trips['main_mode'], normalize='index') * 100
print(mode_by_dist_pct.round(2))

# Focus on external trips (>30km)
print("\n3. External trips (>30km) analysis:")
external = trips[trips['distance_km'] > 30]
print(f"   External trip count: {len(external):,}")
print(f"   Mode distribution:")
external_modes = external['main_mode'].value_counts()
print(external_modes)
print("\n   Mode percentages:")
print((external_modes / len(external) * 100).round(2))

# Check PT in external trips
pt_external = external[external['main_mode'] == 'pt']
print(f"\n4. PT trips in external area: {len(pt_external)}")

# Save summary
print("\n5. Summary saved.")
