import gzip
import xml.etree.ElementTree as ET
import pandas as pd
from sklearn.cluster import KMeans
import glob

# Configuration
BASE_DIR = "output/jeonggwan-v6-regional-multimode"
N_CLUSTERS = 3 # Look for 3 main problem areas

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
print(f"Clustering Gaps in: {PLANS_FILE}")

def get_distance(x1, y1, x2, y2):
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

origins = []
destinations = []

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
                                if dist > 10000:
                                    origins.append([x1, y1])
                                    destinations.append([x2, y2])
                            except: pass
            if elem.tag == 'person': elem.clear()

    import json
    results = {"origins": [], "destinations": []}

    def analyze_points(points, name, key):
        if points:
            df = pd.DataFrame(points, columns=['x', 'y'])
            kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42).fit(df)
            centers = kmeans.cluster_centers_
            
            print(f"\nIdentified {N_CLUSTERS} Main {name} Gap Clusters:")
            for i, center in enumerate(centers):
                coord = {"id": i+1, "x": center[0], "y": center[1], "count": int(sum(kmeans.labels_ == i))}
                results[key].append(coord)
                print(f"[{name} Cluster {i+1}] X={center[0]:.1f}, Y={center[1]:.1f}")
        else:
            print(f"No problematic {name} points found.")

    analyze_points(origins, "Origin", "origins")
    analyze_points(destinations, "Destination", "destinations")
    
    with open('output/gap_clusters_od.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2)
    print("Saved clustering results to output/gap_clusters_od.json")
        
except Exception as e:
    print(f"Error: {e}")
