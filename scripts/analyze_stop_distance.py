import pandas as pd
import xml.etree.ElementTree as ET
from scipy.spatial import cKDTree
import matplotlib.pyplot as plt
import json
import numpy as np

# Configuration
TRANSIT_SCHEDULE_FILE = "input/regional-transit-schedule.xml"
GAP_CLUSTERS_FILE = "output/gap_clusters_od.json"
OUTPUT_PLOT = "output/stop_distance_comparison.png"

print("1. Loading Transit Stops from Regional Schedule...")
stops = []
tree = ET.parse(TRANSIT_SCHEDULE_FILE)
root = tree.getroot()
for stop in root.find('transitStops').findall('stopFacility'):
    stops.append({
        'id': stop.get('id'),
        'x': float(stop.get('x')),
        'y': float(stop.get('y'))
    })
df_stops = pd.DataFrame(stops)
print(f"   Loaded {len(df_stops)} transit stops.")

# Build KD-Tree for fast nearest neighbor search
stops_tree = cKDTree(df_stops[['x', 'y']].values)

print("2. Loading Gap Clusters...")
with open(GAP_CLUSTERS_FILE, 'r', encoding='utf-8') as f:
    clusters = json.load(f)

print("\n" + "="*60)
print("3. Calculating Nearest Stop Distance for Each Cluster:")
print("="*60)

results = []

for cluster_type, cluster_list in clusters.items():
    print(f"\n[{cluster_type.upper()}]")
    for c in cluster_list:
        dist, idx = stops_tree.query([c['x'], c['y']])
        nearest_stop = df_stops.iloc[idx]
        c['nearest_stop_dist'] = dist
        c['nearest_stop_id'] = nearest_stop['id']
        results.append({
            'type': cluster_type,
            'id': c['id'],
            'x': c['x'],
            'y': c['y'],
            'count': c['count'],
            'dist_to_stop': dist
        })
        print(f"  Cluster {c['id']}: ({c['x']:.0f}, {c['y']:.0f})")
        print(f"    -> Nearest Stop: {nearest_stop['id']} at **{dist:.0f}m** ({dist/1000:.1f}km)")

# Summary Table
print("\n" + "="*60)
print("4. SUMMARY: Is Physical Distance the Problem?")
print("="*60)
df_results = pd.DataFrame(results)
print(df_results[['type', 'id', 'count', 'dist_to_stop']].to_string(index=False))

# Interpretation
max_dist = df_results['dist_to_stop'].max()
if max_dist < 2000:
    print(f"\n>> 모든 클러스터가 정류장에서 2km 이내입니다.")
    print(">> 물리적 거리는 문제가 아닙니다. 대신 '노선 연결성(환승)' 또는 '배차간격' 문제일 가능성이 큽니다.")
else:
    far_clusters = df_results[df_results['dist_to_stop'] > 2000]
    print(f"\n>> {len(far_clusters)}개 클러스터가 정류장에서 2km 이상 떨어져 있습니다:")
    print(far_clusters[['type', 'id', 'dist_to_stop']].to_string(index=False))

# 5. Visualization
print("\n5. Generating Visualization...")
plt.figure(figsize=(14, 12))

# Plot stops
plt.scatter(df_stops['x'], df_stops['y'], c='blue', s=3, alpha=0.1, label='Transit Stops')

# Plot cluster centroids
origins = [c for c in clusters['origins']]
destinations = [c for c in clusters['destinations']]

for o in origins:
    plt.scatter(o['x'], o['y'], c='red', s=o['count']/10, marker='o', edgecolors='black', linewidths=1)
    plt.annotate(f"O{o['id']}\n{o['nearest_stop_dist']/1000:.1f}km", (o['x'], o['y']), fontsize=9, color='red')

for d in destinations:
    plt.scatter(d['x'], d['y'], c='green', s=d['count']/10, marker='s', edgecolors='black', linewidths=1)
    plt.annotate(f"D{d['id']}\n{d['nearest_stop_dist']/1000:.1f}km", (d['x'], d['y']), fontsize=9, color='green')

plt.title("Transit Stop Distance Analysis\nRed=Origin Clusters, Green=Destination Clusters, Blue=Transit Stops")
plt.xlabel("X Coordinate")
plt.ylabel("Y Coordinate")
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.savefig(OUTPUT_PLOT, dpi=150)
print(f"   Saved to {OUTPUT_PLOT}")

# Save results to JSON
with open('output/stop_distance_results.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print("   Saved results to output/stop_distance_results.json")

