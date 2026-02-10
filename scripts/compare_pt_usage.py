"""
Compare PT usage between jeonggwan-multimode (original) and jeonggwan-v1-multimode (regional network)
"""
import gzip
import pandas as pd

def analyze_trips(folder_name, output_file):
    """Analyze mode distribution by distance"""
    print(f"\n{'='*60}")
    print(f"Analyzing: {folder_name}")
    print(f"{'='*60}")
    
    with gzip.open(f"output/{folder_name}/{output_file}", 'rt') as f:
        trips = pd.read_csv(f, sep=';')
    
    print(f"Total trips: {len(trips):,}")
    
    trips['distance_km'] = trips['traveled_distance'] / 1000
    
    def categorize_distance(d):
        if d < 5:
            return "1. Local (<5km)"
        elif d < 15:
            return "2. Short (5-15km)"
        elif d < 30:
            return "3. Medium (15-30km)"
        else:
            return "4. Long (>30km)"
    
    trips['distance_cat'] = trips['distance_km'].apply(categorize_distance)
    
    # Mode distribution by distance
    mode_by_dist_pct = pd.crosstab(trips['distance_cat'], trips['main_mode'], normalize='index') * 100
    
    print("\n--- Mode Distribution by Distance (%) ---")
    print(mode_by_dist_pct.round(2).to_string())
    
    # Trip counts by category
    print("\n--- Trip Counts by Distance Category ---")
    print(trips['distance_cat'].value_counts().sort_index())
    
    return mode_by_dist_pct, trips

# Analyze original (jeonggwan-multimode)
print("\n" + "="*70)
print("COMPARISON: Original vs. Regional Network PT Usage")
print("="*70)

old_pct, old_trips = analyze_trips("jeonggwan-multimode", "null-multimode.output_trips.csv.gz")
new_pct, new_trips = analyze_trips("jeonggwan-v1-multimode", "null-multimode.output_trips.csv.gz")

# Compare external trips
print("\n" + "="*70)
print("COMPARISON SUMMARY: Long-distance Trips (>30km)")
print("="*70)

print("\n--- Original (jeonggwan-multimode) ---")
if "4. Long (>30km)" in old_pct.index:
    print(old_pct.loc["4. Long (>30km)"].round(2))
else:
    print("No long-distance trips found!")

print("\n--- Regional Network (jeonggwan-v1-multimode) ---")
if "4. Long (>30km)" in new_pct.index:
    print(new_pct.loc["4. Long (>30km)"].round(2))
else:
    print("No long-distance trips found!")

print("\n✅ Analysis Complete!")
