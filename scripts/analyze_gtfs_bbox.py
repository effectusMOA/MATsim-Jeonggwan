import pandas as pd
import os

GTFS_DIR = "input/jeonggwan-gtfs"

def analyze_bbox():
    stops_file = os.path.join(GTFS_DIR, "stops.txt")
    if not os.path.exists(stops_file):
        print(f"Error: {stops_file} not found.")
        return

    print("Loading stops...")
    stops = pd.read_csv(stops_file)
    
    min_lon = stops['stop_lon'].min()
    max_lon = stops['stop_lon'].max()
    min_lat = stops['stop_lat'].min()
    max_lat = stops['stop_lat'].max()
    
    print("\n=== GTFS Coverage BBox ===")
    print(f"Longitude: {min_lon:.4f} ~ {max_lon:.4f}")
    print(f"Latitude:  {min_lat:.4f} ~ {max_lat:.4f}")
    
    # Check coverage of major cities
    cities = {
        'Busan (Center)': (129.0, 35.1),
        'Ulsan (Center)': (129.3, 35.5),
        'Yangsan (Center)': (129.0, 35.3),
        'Seoul (Gangnam)': (127.0, 37.5)
    }
    
    print("\n=== Major City Coverage Check ===")
    for city, (lon, lat) in cities.items():
        covered = (min_lon <= lon <= max_lon) and (min_lat <= lat <= max_lat)
        print(f"{city}: {'Covered' if covered else 'Outside'}")

if __name__ == "__main__":
    analyze_bbox()
