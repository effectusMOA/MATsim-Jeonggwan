import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

plans_file = "input/jeonggwan-plans-v4.xml"
log_file = "input/plans_analysis_log.txt"

def log_print(msg):
    print(msg)
    with open(log_file, 'a') as f:
        f.write(msg + '\n')

with open(log_file, 'w') as f:
    f.write("Starting analysis...\n")

log_print(f"Reading plans file: {plans_file}")

# Parse XML (iterative parsing to save memory)
context = ET.iterparse(plans_file, events=('end',))

# Coordinates accumulating
x_coords = []
y_coords = []
act_types = []

log_print("Parsing XML... this may take a moment.")
count = 0
for event, elem in context:
    if elem.tag == 'activity':
        try:
            x = float(elem.attrib['x'])
            y = float(elem.attrib['y'])
            act_type = elem.attrib['type']
            
            x_coords.append(x)
            y_coords.append(y)
            act_types.append(act_type)
            count += 1
            
            if count % 100000 == 0:
                log_print(f"Processed {count} activities...")
                
        except KeyError:
            pass # Start/end activities might not have coords if link-based only
    
    elem.clear()

log_print(f"Total activities extracted: {len(x_coords)}")

df = pd.DataFrame({
    'x': x_coords,
    'y': y_coords,
    'type': act_types
})

# Filter for Home and Work/Education to see distribution
home_df = df[df['type'] == 'home']
work_df = df[df['type'].isin(['work', 'education'])]

log_print(f"Home activities: {len(home_df)}")
log_print(f"Work/Edu activities: {len(work_df)}")

# Calculate bounds
min_x, max_x = df['x'].min(), df['x'].max()
min_y, max_y = df['y'].min(), df['y'].max()

log_print(f"Coordinate Bounds:")
log_print(f"X: {min_x:,.1f} ~ {max_x:,.1f}")
log_print(f"Y: {min_y:,.1f} ~ {max_y:,.1f}")

# Plotting
fig, ax = plt.subplots(figsize=(12, 12))

# Sample if too large
plot_df = df.sample(min(50000, len(df))) if len(df) > 0 else df

# Plot activities
ax.scatter(plot_df['x'], plot_df['y'], s=1, alpha=0.3, label='Activity Locations')

# Jeonggwan Center (Approx)
jg_x, jg_y = 1152000, 1704000
ax.plot(jg_x, jg_y, 'ro', markersize=10, label='Jeonggwan Center')

# Add circles for range
circles = [5000, 10000, 20000, 30000] # 5km, 10km, 20km, 30km
for r in circles:
    circle = plt.Circle((jg_x, jg_y), r, fill=False, color='red', linestyle='--', alpha=0.5, label=f'{r/1000}km Radius')
    ax.add_patch(circle)

ax.set_title(f"Activity Location Distribution (Total: {len(df):,})")
ax.set_xlabel("X (EPSG:5179)")
ax.set_ylabel("Y (EPSG:5179)")
ax.legend()
ax.grid(True)
ax.set_aspect('equal')

output_img = "input/plans_activity_distribution.png"
plt.savefig(output_img, dpi=150)
log_print(f"Saved plot to {output_img}")
