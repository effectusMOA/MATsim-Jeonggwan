import gzip
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import glob
import os

# Configuration
BASE_DIR = "output/jeonggwan-v6-regional-multimode"
TRANSIT_SCHEDULE_FILE = "input/regional-transit-schedule.xml"
OUTPUT_PLOT = "output/gtfs_gap_analysis.png"

# Find latest plans file
def get_latest_plans_file(base_dir):
    plans_files = glob.glob(f"{base_dir}/ITERS/it.*/???.plans.xml.gz") + glob.glob(f"{base_dir}/ITERS/it.*/*.plans.xml.gz")
    if not plans_files:
        if glob.glob(f"{base_dir}/*.output_plans.xml.gz"):
            return glob.glob(f"{base_dir}/*.output_plans.xml.gz")[0]
        return None
    
    def extract_iter(f):
        try:
            return int(f.split('it.')[1].split('\\')[0].split('/')[0])
        except:
            return -1
    plans_files.sort(key=extract_iter)
    return plans_files[-1]

PLANS_FILE = get_latest_plans_file(BASE_DIR)
print(f"Analyzing Plans File: {PLANS_FILE}")

def get_distance(x1, y1, x2, y2):
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

# 1. Load Existing Transit Stops
print("Loading Transit Schedule...")
stops = []
try:
    tree = ET.parse(TRANSIT_SCHEDULE_FILE)
    root = tree.getroot()
    for stop in root.find('transitStops').findall('stopFacility'):
        stops.append({
            'x': float(stop.get('x')),
            'y': float(stop.get('y'))
        })
    print(f"Loaded {len(stops)} transit stops.")
except Exception as e:
    print(f"Error loading transit schedule: {e}")
    stops = []

df_stops = pd.DataFrame(stops)

# 2. Extract Problematic O/D Pairs (Walk > 10km)
print("Extracting Problematic O/D Pairs...")
od_points = [] # list of {'x':, 'y':, 'type': 'O' or 'D'}

try:
    with gzip.open(PLANS_FILE, 'rt', encoding='utf-8') as f:
        context = ET.iterparse(f, events=('end',))
        
        for event, elem in context:
            if elem.tag == 'plan' and elem.get('selected') == 'yes':
                legs = elem.findall('leg')
                activities = elem.findall('activity')
                
                for i, leg in enumerate(legs):
                    if leg.get('mode') == 'walk':
                        if i < len(activities) - 1:
                            act_from = activities[i]
                            act_to = activities[i+1]
                            try:
                                x1, y1 = float(act_from.get('x')), float(act_from.get('y'))
                                x2, y2 = float(act_to.get('x')), float(act_to.get('y'))
                                dist = get_distance(x1, y1, x2, y2)
                                
                                if dist > 10000: # 10km threshold
                                    od_points.append({'x': x1, 'y': y1, 'type': 'Origin'})
                                    od_points.append({'x': x2, 'y': y2, 'type': 'Dest'})
                            except:
                                pass
            
            if elem.tag == 'person':
                elem.clear()
                
    df_od = pd.DataFrame(od_points)
    print(f"Found {len(df_od)//2} problematic trips ({len(df_od)} points).")

    # 3. Visualization
    print("Generating Visualization...")
    plt.figure(figsize=(12, 10))
    
    # Plot Problematic Points
    # Sample if too many points to avoid clutter, specific to analyze distribution
    if len(df_od) > 10000:
        plot_data = df_od.sample(10000)
    else:
        plot_data = df_od
        
    plt.scatter(plot_data['x'], plot_data['y'], c='red', s=5, alpha=0.3, label='Problematic O/D (Walk > 10km)')
    
    # Plot Existing Stops
    if not df_stops.empty:
        plt.scatter(df_stops['x'], df_stops['y'], c='blue', s=20, alpha=0.5, marker='^', label='Existing Transit Stops')
    
    plt.title(f"GTFS Coverage Gap Analysis\nRed: Locations requiring connectivity (Walk > 10km) | Blue: Current Stops")
    plt.xlabel("X Coordinate")
    plt.ylabel("Y Coordinate")
    plt.legend()
    plt.grid(True)
    plt.axis('equal')
    
    plt.savefig(OUTPUT_PLOT)
    print(f"Saved visualization to {OUTPUT_PLOT}")
    
    # Calculate Bounding Box of Gaps
    if not df_od.empty:
        min_x, max_x = df_od['x'].min(), df_od['x'].max()
        min_y, max_y = df_od['y'].min(), df_od['y'].max()
        print("\nProblematic Area Bounds:")
        print(f"X: {min_x:.1f} ~ {max_x:.1f}")
        print(f"Y: {min_y:.1f} ~ {max_y:.1f}")
        
except Exception as e:
    print(f"Error: {e}")
