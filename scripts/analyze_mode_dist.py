import pandas as pd
import gzip
import os

# Configuration
trips_file = 'output/jeonggwan-v3-multimode-multimode/null-multimode.output_trips.csv.gz'
output_dir = 'output/jeonggwan-v3-multimode-multimode'

def analyze_mode_by_distance():
    print(f"Reading {trips_file}...")
    
    # Check if file exists
    if not os.path.exists(trips_file):
        print(f"Error: File {trips_file} not found.")
        return

    try:
        with gzip.open(trips_file, 'rt', encoding='utf-8') as f:
            # Try reading first line to detect separator
            first_line = f.readline()
            sep = ';' if ';' in first_line else ','
            f.seek(0)
            df = pd.read_csv(f, sep=sep)
    except Exception as e:
        print(f"Error reading CSV: {e}")
        return

    print("Columns:", df.columns.tolist())
    
    # Ensure relevant columns exist
    # Standard MATSim trips file usually has 'main_mode' and 'traveled_distance' (or similar)
    # If traveled_distance is missing, we might need to calculate beeline from coords
    
    dist_col = 'traveled_distance'
    mode_col = 'main_mode'
    
    if dist_col not in df.columns:
        print(f"'{dist_col}' column not found. Available: {df.columns}")
        # Try to find a distance column
        for c in df.columns:
            if 'dist' in c.lower():
                dist_col = c
                print(f"Using '{dist_col}' as distance column.")
                break
    
    if mode_col not in df.columns:
        print(f"'{mode_col}' column not found. Available: {df.columns}")
        return

    # Filter out non-travel modes if any (though output_trips usually only has travel modes)
    
    # Define Distance Bins (in meters)
    bins = [0, 1000, 2000, 3000, 5000, 10000, 50000]
    labels = ['0-1km', '1-2km', '2-3km', '3-5km', '5-10km', '10km+']
    
    df['dist_bin'] = pd.cut(df[dist_col], bins=bins, labels=labels, right=False)
    
    # Group by bin and mode
    result = df.groupby(['dist_bin', mode_col], observed=False).size().unstack(fill_value=0)
    
    # Calculate percentages per bin (row-wise)
    result_pct = result.div(result.sum(axis=1), axis=0) * 100
    
    print("\n=== Mode Share by Distance (Count) ===")
    print(result)
    
    print("\n=== Mode Share by Distance (%) ===")
    print(result_pct.round(1))
    
    # Calculate total share per bin
    bin_counts = df['dist_bin'].value_counts().sort_index()
    bin_share = (bin_counts / len(df)) * 100
    print("\n=== Trip Distance Distribution (%) ===")
    print(bin_share.round(1))

    # Save to CSV for reference
    result_pct.to_csv(os.path.join(output_dir, 'mode_share_by_distance.csv'))
    print(f"\nSaved analysis to {os.path.join(output_dir, 'mode_share_by_distance.csv')}")

if __name__ == "__main__":
    analyze_mode_by_distance()
