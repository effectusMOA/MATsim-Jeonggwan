"""
Analyze and visualize agent coordinate distribution in plans file
Explain what "Core Area" means
"""
import gzip
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from pyproj import Transformer
import numpy as np

print("="*70)
print("                    에이전트 좌표 분석")
print("="*70)

# Load activities from output
print("\n1. Loading activities data...")
with gzip.open("output/jeonggwan-v1-multimode/null-multimode.output_activities.csv.gz", 'rt') as f:
    activities = pd.read_csv(f, sep=';')

print(f"   Total activities: {len(activities):,}")
print(f"   Unique persons: {activities['person'].nunique():,}")

# Get unique activity locations
home_activities = activities[activities['activity_type'] == 'home']
work_activities = activities[activities['activity_type'] == 'work']

print(f"\n2. Activity locations:")
print(f"   Home activities: {len(home_activities):,}")
print(f"   Work activities: {len(work_activities):,}")

# Calculate coordinate ranges
print(f"\n3. Coordinate ranges (EPSG:5179):")
print(f"   Home X: {home_activities['coord_x'].min():.0f} ~ {home_activities['coord_x'].max():.0f}")
print(f"   Home Y: {home_activities['coord_y'].min():.0f} ~ {home_activities['coord_y'].max():.0f}")
print(f"   Work X: {work_activities['coord_x'].min():.0f} ~ {work_activities['coord_x'].max():.0f}")
print(f"   Work Y: {work_activities['coord_y'].min():.0f} ~ {work_activities['coord_y'].max():.0f}")

# Define regions
print("\n" + "="*70)
print("                    지역 정의 (CORE AREA 설명)")
print("="*70)

# Original network BBox (before expansion)
# create_moct_network.py had:
# 'minx': 128.9, 'miny': 35.15, 'maxx': 129.35, 'maxy': 35.45
# This is the ORIGINAL Jeonggwan study area

# Expanded network BBox:
# 'minx': 128.5, 'miny': 35.0, 'maxx': 129.6, 'maxy': 36.1

# Convert to EPSG:5179
transformer = Transformer.from_crs("EPSG:4326", "EPSG:5179", always_xy=True)

# Original (Core) area - Jeonggwan + Yangsan + part of Busan
orig_x_min, orig_y_min = transformer.transform(128.9, 35.15)
orig_x_max, orig_y_max = transformer.transform(129.35, 35.45)

# Expanded area - includes 김해, 경주, 포항, 밀양, 창원
exp_x_min, exp_y_min = transformer.transform(128.5, 35.0)
exp_x_max, exp_y_max = transformer.transform(129.6, 36.1)

print(f"""
📍 CORE AREA (원래 연구 지역):
   정의: 기존 정관읍/양산/부산 일부 지역
   WGS84: 128.9°~129.35°E, 35.15°~35.45°N
   EPSG:5179: X={orig_x_min:.0f}~{orig_x_max:.0f}, Y={orig_y_min:.0f}~{orig_y_max:.0f}
   
📍 EXPANDED AREA (확장된 광역 네트워크):
   정의: 김해, 경주, 포항, 밀양, 창원 포함
   WGS84: 128.5°~129.6°E, 35.0°~36.1°N
   EPSG:5179: X={exp_x_min:.0f}~{exp_x_max:.0f}, Y={exp_y_min:.0f}~{exp_y_max:.0f}
""")

# Check how many agents are in each region
def classify_location(x, y):
    in_core = (orig_x_min <= x <= orig_x_max) and (orig_y_min <= y <= orig_y_max)
    in_expanded = (exp_x_min <= x <= exp_x_max) and (exp_y_min <= y <= exp_y_max)
    
    if in_core:
        return "Core Area (정관읍/양산)"
    elif in_expanded:
        return "Expanded Area (광역 네트워크)"
    else:
        return "Outside Network"

home_activities = home_activities.copy()
home_activities['region'] = home_activities.apply(
    lambda r: classify_location(r['coord_x'], r['coord_y']), axis=1
)

print("\n4. 에이전트 Home 위치 분포:")
region_dist = home_activities['region'].value_counts()
print(region_dist)
print("\n   비율:")
print((region_dist / len(home_activities) * 100).round(2))

# Create visualization
print("\n5. Creating visualization...")
fig, ax = plt.subplots(figsize=(14, 12))

# Sample for visualization (too many points)
sample_size = min(10000, len(home_activities))
home_sample = home_activities.sample(sample_size)

# Plot home locations
ax.scatter(home_sample['coord_x'], home_sample['coord_y'], c='blue', s=2, alpha=0.3, label='Home locations')

# Draw Core Area rectangle
core_rect = patches.Rectangle(
    (orig_x_min, orig_y_min), 
    orig_x_max - orig_x_min, 
    orig_y_max - orig_y_min,
    linewidth=3, edgecolor='red', facecolor='none', 
    label='Core Area (Original Network)'
)
ax.add_patch(core_rect)

# Draw Expanded Area rectangle
exp_rect = patches.Rectangle(
    (exp_x_min, exp_y_min),
    exp_x_max - exp_x_min,
    exp_y_max - exp_y_min,
    linewidth=2, edgecolor='green', facecolor='none', linestyle='--',
    label='Expanded Area (Regional Network)'
)
ax.add_patch(exp_rect)

ax.set_xlim(exp_x_min - 10000, exp_x_max + 10000)
ax.set_ylim(exp_y_min - 10000, exp_y_max + 10000)
ax.set_xlabel('X (EPSG:5179)', fontsize=12)
ax.set_ylabel('Y (EPSG:5179)', fontsize=12)
ax.set_title('에이전트 Home 위치 분포 vs. 네트워크 영역', fontsize=14, fontweight='bold')
ax.legend(loc='upper left', fontsize=10)
ax.set_aspect('equal')
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.savefig("input/agent_coordinate_distribution.png", dpi=150, facecolor='white')
print("   Saved to: input/agent_coordinate_distribution.png")

print("\n" + "="*70)
print("                         분석 완료!")
print("="*70)
