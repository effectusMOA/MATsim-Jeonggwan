
import xml.etree.ElementTree as ET
import gzip
import pandas as pd
import matplotlib.pyplot as plt
import os

plans_file = 'output/jeonggwan-v5-multimode/ITERS/it.10/null-multimode.10.plans.xml.gz'
output_png = 'output/jeonggwan-v5-multimode/distance_mode_split_v5.png'

print(f"Reading {plans_file}...")

data = []

with gzip.open(plans_file, 'rb') as f:
    context = ET.iterparse(f, events=('start', 'end'))
    current_person_id = None
    
    for event, elem in context:
        if event == 'start' and elem.tag == 'person':
            current_person_id = elem.get('id')
        elif event == 'end' and elem.tag == 'leg':
            mode = elem.get('mode')
            # Extract distance from route if available
            route = elem.find('route')
            dist = 0
            if route is not None:
                dist_str = route.get('distance')
                if dist_str:
                    dist = float(dist_str)
            
            if dist > 0:
                data.append({'person': current_person_id, 'mode': mode, 'distance': dist})
            elem.clear()
        elif event == 'end' and elem.tag == 'person':
            elem.clear()

df = pd.DataFrame(data)

# Define distance bins (in meters)
bins = [0, 1000, 2000, 5000, 10000, 20000, 50000, float('inf')]
labels = ['0-1km', '1-2km', '2-5km', '5-10km', '10-20km', '20-50km', '50km+']
df['dist_bin'] = pd.cut(df['distance'], bins=bins, labels=labels)

# Calculate proportions
dist_stats = df.groupby(['dist_bin', 'mode'], observed=False).size().unstack(fill_value=0)
dist_props = dist_stats.div(dist_stats.sum(axis=1), axis=0)

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

print("\nMode Share by Distance Bin:")
print(dist_props)

with open('output/jeonggwan-v5-multimode/distance_stats_v5.txt', 'w') as f:
    f.write(dist_props.to_string())

# Plotting
ax = dist_props.plot(kind='bar', stacked=True, figsize=(10, 6), colormap='viridis')
plt.title('Mode Share by Distance (V5 Iteration 10)')
plt.xlabel('Distance Bin')
plt.ylabel('Share')
plt.legend(title='Mode', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.grid(axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(output_png)
print(f"\nPlot saved to {output_png}")
