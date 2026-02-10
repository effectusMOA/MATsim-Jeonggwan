"""
Jeonggwan v6 Baseline Simulation - Comprehensive Visualization
Generates 6 charts from simulation output data:
1. Mode Share Trend
2. Score Convergence
3. Trip Distance Distribution by Mode
4. Long-Distance Walk OD Heatmap
5. Subpopulation Mode Share
6. Departure Time Distribution
"""
import gzip
import xml.etree.ElementTree as ET
import json
import math
import os
from collections import defaultdict, Counter

# Try importing plotting libraries
try:
    import matplotlib
    matplotlib.use('Agg')  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.ticker as ticker
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False
    print("WARNING: matplotlib not found. Install with: pip install matplotlib numpy")

# Configuration
OUTPUT_DIR = "output/jeonggwan-v6-v6-baseline"
PLANS_FILE = f"{OUTPUT_DIR}/ITERS/it.90/90.plans.xml.gz"
VIS_DIR = f"{OUTPUT_DIR}/visualizations"

# Create output directory
os.makedirs(VIS_DIR, exist_ok=True)

# Korean-friendly font setup
plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans', 'sans-serif'] 
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

# Color palette
COLORS = {
    'car': '#E74C3C',
    'pt': '#3498DB',
    'walk': '#2ECC71',
    'drt': '#F39C12',
    'sav': '#9B59B6',
}
SUBPOP_COLORS = {
    'young': '#3498DB',
    'elderly': '#E74C3C',
    'default': '#2ECC71',
    '': '#95A5A6',
}


# ============================================================
# 1. MODE SHARE TREND
# ============================================================
def plot_mode_share_trend():
    print("1. Generating Mode Share Trend...")
    import csv
    data = {'iteration': [], 'car': [], 'pt': [], 'walk': []}
    
    with open(f"{OUTPUT_DIR}/modestats.csv", 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            data['iteration'].append(int(row['iteration']))
            data['car'].append(float(row['car']))
            data['pt'].append(float(row['pt']))
            data['walk'].append(float(row['walk']))
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.fill_between(data['iteration'], 0, data['car'], alpha=0.3, color=COLORS['car'])
    ax.fill_between(data['iteration'], data['car'], 
                    [c+p for c,p in zip(data['car'], data['pt'])], alpha=0.3, color=COLORS['pt'])
    ax.fill_between(data['iteration'], 
                    [c+p for c,p in zip(data['car'], data['pt'])],
                    [c+p+w for c,p,w in zip(data['car'], data['pt'], data['walk'])], 
                    alpha=0.3, color=COLORS['walk'])
    
    ax.plot(data['iteration'], data['car'], color=COLORS['car'], linewidth=2, label=f"Car ({data['car'][-1]:.1%})")
    ax.plot(data['iteration'], data['pt'], color=COLORS['pt'], linewidth=2, label=f"PT ({data['pt'][-1]:.1%})")
    ax.plot(data['iteration'], data['walk'], color=COLORS['walk'], linewidth=2, label=f"Walk ({data['walk'][-1]:.1%})")
    
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Mode Share', fontsize=12)
    ax.set_title('Mode Share Trend - Jeonggwan v6 Baseline', fontsize=14, fontweight='bold')
    ax.legend(loc='right', fontsize=11)
    ax.set_ylim(0, 0.75)
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, max(data['iteration']))
    
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/01_mode_share_trend.png")
    plt.close()
    print(f"   Saved: {VIS_DIR}/01_mode_share_trend.png")
    
    # Also make a pie chart for final iteration
    fig, ax = plt.subplots(figsize=(8, 8))
    labels = ['Car', 'PT', 'Walk']
    sizes = [data['car'][-1], data['pt'][-1], data['walk'][-1]]
    colors = [COLORS['car'], COLORS['pt'], COLORS['walk']]
    explode = (0.02, 0.02, 0.05)
    
    wedges, texts, autotexts = ax.pie(sizes, explode=explode, labels=labels, colors=colors,
                                       autopct='%1.1f%%', shadow=False, startangle=90,
                                       textprops={'fontsize': 13})
    for autotext in autotexts:
        autotext.set_fontweight('bold')
    ax.set_title(f'Final Mode Share (Iteration {data["iteration"][-1]})', fontsize=14, fontweight='bold')
    
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/01b_mode_share_pie.png")
    plt.close()
    print(f"   Saved: {VIS_DIR}/01b_mode_share_pie.png")


# ============================================================
# 2. SCORE CONVERGENCE
# ============================================================
def plot_score_convergence():
    print("2. Generating Score Convergence...")
    import csv
    data = {'iteration': [], 'avg_executed': [], 'avg_worst': [], 'avg_best': []}
    
    with open(f"{OUTPUT_DIR}/scorestats.csv", 'r') as f:
        reader = csv.DictReader(f, delimiter=';')
        for row in reader:
            data['iteration'].append(int(row['iteration']))
            data['avg_executed'].append(float(row['avg_executed']))
            data['avg_worst'].append(float(row['avg_worst']))
            data['avg_best'].append(float(row['avg_best']))
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    ax.plot(data['iteration'], data['avg_best'], color='#27AE60', linewidth=1.5, 
            alpha=0.7, label='Best')
    ax.plot(data['iteration'], data['avg_executed'], color='#2980B9', linewidth=2.5, 
            label='Executed (Selected)')
    ax.plot(data['iteration'], data['avg_worst'], color='#E74C3C', linewidth=1.5, 
            alpha=0.7, label='Worst')
    
    ax.fill_between(data['iteration'], data['avg_worst'], data['avg_best'], 
                    alpha=0.1, color='#3498DB')
    
    ax.set_xlabel('Iteration', fontsize=12)
    ax.set_ylabel('Average Score', fontsize=12)
    ax.set_title('Score Convergence - Jeonggwan v6 Baseline', fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/02_score_convergence.png")
    plt.close()
    print(f"   Saved: {VIS_DIR}/02_score_convergence.png")


# ============================================================
# 3-6. PLANS-BASED ANALYSES (parse once, generate multiple)
# ============================================================
def parse_plans_and_visualize():
    print("3-6. Parsing plans file for detailed analysis...")
    
    # Data collectors
    trips = []  # {mode, distance, origin_x, origin_y, dest_x, dest_y, dep_time, subpop, carAvail}
    mode_by_subpop = defaultdict(Counter)
    
    total_persons = 0
    
    with gzip.open(PLANS_FILE, 'rb') as f:
        context = ET.iterparse(f, events=['start', 'end'])
        current_person = None
        current_plan_selected = False
        current_activities = []
        current_legs = []
        person_attrs = {}
        
        for event, elem in context:
            if event == 'start' and elem.tag == 'person':
                current_person = elem.get('id')
                total_persons += 1
                person_attrs = {}
                
            elif event == 'start' and elem.tag == 'attribute' and current_person:
                name = elem.get('name')
                if name and elem.text:
                    person_attrs[name] = elem.text
                
            elif event == 'start' and elem.tag == 'plan':
                current_plan_selected = elem.get('selected') == 'yes'
                current_activities = []
                current_legs = []
                
            elif event == 'start' and elem.tag == 'activity' and current_plan_selected:
                act_type = elem.get('type')
                x = elem.get('x')
                y = elem.get('y')
                if x and y:
                    current_activities.append({
                        'type': act_type, 'x': float(x), 'y': float(y)
                    })
                    
            elif event == 'start' and elem.tag == 'leg' and current_plan_selected:
                current_legs.append({
                    'mode': elem.get('mode'),
                    'dep_time': elem.get('dep_time')
                })
                
            elif event == 'end' and elem.tag == 'plan' and current_plan_selected:
                subpop = person_attrs.get('subpopulation', '')
                car_avail = person_attrs.get('carAvail', '')
                
                for i, leg in enumerate(current_legs):
                    if i < len(current_activities) - 1:
                        origin = current_activities[i]
                        dest = current_activities[i+1]
                        dx = origin['x'] - dest['x']
                        dy = origin['y'] - dest['y']
                        dist = math.sqrt(dx*dx + dy*dy)
                        
                        trips.append({
                            'mode': leg['mode'],
                            'distance': dist,
                            'origin_x': origin['x'],
                            'origin_y': origin['y'],
                            'dest_x': dest['x'],
                            'dest_y': dest['y'],
                            'origin_type': origin['type'],
                            'dest_type': dest['type'],
                            'dep_time': leg['dep_time'],
                            'subpop': subpop,
                            'carAvail': car_avail
                        })
                        
                        mode_by_subpop[subpop][leg['mode']] += 1
                
            elif event == 'end' and elem.tag == 'person':
                current_person = None
                elem.clear()
    
    print(f"   Parsed {total_persons} persons, {len(trips)} trips")
    
    # ============================================================
    # 3. TRIP DISTANCE DISTRIBUTION BY MODE
    # ============================================================
    print("3. Generating Trip Distance Distribution...")
    
    fig, axes = plt.subplots(1, 3, figsize=(18, 6))
    
    modes = ['car', 'pt', 'walk']
    dist_bins = np.arange(0, 80001, 2000)  # 0 to 80km in 2km bins
    
    for ax, mode in zip(axes, modes):
        mode_dists = [t['distance']/1000 for t in trips if t['mode'] == mode]
        
        ax.hist(mode_dists, bins=40, range=(0, 80), color=COLORS[mode], 
                alpha=0.7, edgecolor='white', linewidth=0.5)
        
        median_d = np.median(mode_dists) if mode_dists else 0
        mean_d = np.mean(mode_dists) if mode_dists else 0
        
        ax.axvline(median_d, color='black', linestyle='--', linewidth=1.5, 
                   label=f'Median: {median_d:.1f}km')
        ax.axvline(mean_d, color='red', linestyle=':', linewidth=1.5, 
                   label=f'Mean: {mean_d:.1f}km')
        
        if mode == 'walk':
            ax.axvline(10, color='orange', linestyle='-', linewidth=2, 
                       alpha=0.8, label='10km threshold')
        
        ax.set_xlabel('Distance (km)', fontsize=11)
        ax.set_ylabel('Count', fontsize=11)
        ax.set_title(f'{mode.upper()} ({len(mode_dists):,} trips)', fontsize=13, fontweight='bold')
        ax.legend(fontsize=9)
        ax.grid(True, alpha=0.2)
    
    plt.suptitle('Trip Distance Distribution by Mode - Jeonggwan v6 Baseline', 
                 fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/03_trip_distance_distribution.png", bbox_inches='tight')
    plt.close()
    print(f"   Saved: {VIS_DIR}/03_trip_distance_distribution.png")
    
    # ============================================================
    # 4. LONG-DISTANCE WALK OD HEATMAP
    # ============================================================
    print("4. Generating Walk OD Heatmap...")
    
    long_walks = [t for t in trips if t['mode'] == 'walk' and t['distance'] >= 10000]
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 8))
    
    # Origins
    ox = [t['origin_x'] for t in long_walks]
    oy = [t['origin_y'] for t in long_walks]
    h1 = axes[0].hexbin(ox, oy, gridsize=30, cmap='YlOrRd', mincnt=1)
    axes[0].set_title(f'Origins of 10km+ Walks (n={len(long_walks):,})', fontsize=12, fontweight='bold')
    axes[0].set_xlabel('X (EPSG:5179)')
    axes[0].set_ylabel('Y (EPSG:5179)')
    plt.colorbar(h1, ax=axes[0], label='Count')
    
    # Destinations
    dx = [t['dest_x'] for t in long_walks]
    dy = [t['dest_y'] for t in long_walks]
    h2 = axes[1].hexbin(dx, dy, gridsize=30, cmap='YlOrBr', mincnt=1)
    axes[1].set_title(f'Destinations of 10km+ Walks', fontsize=12, fontweight='bold')
    axes[1].set_xlabel('X (EPSG:5179)')
    axes[1].set_ylabel('Y (EPSG:5179)')
    plt.colorbar(h2, ax=axes[1], label='Count')
    
    # Equal axes
    for ax in axes:
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
    
    plt.suptitle('Spatial Distribution of Long-Distance Walk Trips', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/04_walk_od_heatmap.png", bbox_inches='tight')
    plt.close()
    print(f"   Saved: {VIS_DIR}/04_walk_od_heatmap.png")
    
    # OD Lines for top walkers
    fig, ax = plt.subplots(figsize=(12, 10))
    
    # Background: all activities
    all_x = [t['origin_x'] for t in trips[:5000]]
    all_y = [t['origin_y'] for t in trips[:5000]]
    ax.scatter(all_x, all_y, c='lightgray', s=1, alpha=0.3, label='Activities')
    
    # Long walks as lines
    for t in sorted(long_walks, key=lambda x: x['distance'])[:500]:
        alpha = min(0.5, t['distance'] / 100000)
        ax.plot([t['origin_x'], t['dest_x']], 
                [t['origin_y'], t['dest_y']], 
                color='red', alpha=alpha, linewidth=0.5)
    
    ax.set_title('Long-Distance Walk OD Lines (10km+, sample 500)', fontsize=13, fontweight='bold')
    ax.set_xlabel('X (EPSG:5179)')
    ax.set_ylabel('Y (EPSG:5179)')
    ax.set_aspect('equal')
    ax.grid(True, alpha=0.2)
    
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/04b_walk_od_lines.png", bbox_inches='tight')
    plt.close()
    print(f"   Saved: {VIS_DIR}/04b_walk_od_lines.png")
    
    # ============================================================
    # 5. SUBPOPULATION MODE SHARE
    # ============================================================
    print("5. Generating Subpopulation Mode Share...")
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 6))
    
    subpops = ['young', 'elderly', '']
    subpop_labels = ['Young', 'Elderly', 'Null/Unknown']
    
    for ax, subpop, label in zip(axes, subpops, subpop_labels):
        counts = mode_by_subpop[subpop]
        total = sum(counts.values())
        if total == 0:
            continue
            
        modes_present = ['car', 'pt', 'walk']
        shares = [counts.get(m, 0) / total for m in modes_present]
        colors = [COLORS.get(m, '#999') for m in modes_present]
        
        bars = ax.bar(modes_present, shares, color=colors, edgecolor='white', linewidth=1)
        
        for bar, share in zip(bars, shares):
            ax.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.01,
                    f'{share:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=11)
        
        ax.set_title(f'{label}\n(n={total:,})', fontsize=12, fontweight='bold')
        ax.set_ylabel('Mode Share')
        ax.set_ylim(0, 0.75)
        ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
        ax.grid(True, alpha=0.2, axis='y')
    
    plt.suptitle('Mode Share by Subpopulation - Jeonggwan v6 Baseline', 
                 fontsize=14, fontweight='bold')
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/05_subpop_mode_share.png", bbox_inches='tight')
    plt.close()
    print(f"   Saved: {VIS_DIR}/05_subpop_mode_share.png")
    
    # Stacked bar with car availability breakdown
    fig, ax = plt.subplots(figsize=(10, 6))
    
    car_avail_groups = defaultdict(Counter)
    for t in trips:
        key = f"{t['subpop']}_{t['carAvail']}"
        car_avail_groups[key][t['mode']] += 1
    
    group_labels = []
    car_shares = []
    pt_shares = []
    walk_shares = []
    
    for subpop in ['young', 'elderly']:
        for avail in ['always', 'never']:
            key = f"{subpop}_{avail}"
            if key in car_avail_groups:
                total = sum(car_avail_groups[key].values())
                group_labels.append(f"{subpop}\n({avail})")
                car_shares.append(car_avail_groups[key].get('car', 0) / total)
                pt_shares.append(car_avail_groups[key].get('pt', 0) / total)
                walk_shares.append(car_avail_groups[key].get('walk', 0) / total)
    
    x = np.arange(len(group_labels))
    width = 0.6
    
    ax.bar(x, car_shares, width, label='Car', color=COLORS['car'])
    ax.bar(x, pt_shares, width, bottom=car_shares, label='PT', color=COLORS['pt'])
    ax.bar(x, walk_shares, width, 
           bottom=[c+p for c,p in zip(car_shares, pt_shares)], 
           label='Walk', color=COLORS['walk'])
    
    ax.set_xticks(x)
    ax.set_xticklabels(group_labels, fontsize=10)
    ax.set_ylabel('Mode Share')
    ax.set_title('Mode Share by Subpopulation & Car Availability', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_formatter(ticker.PercentFormatter(1.0))
    ax.legend()
    ax.grid(True, alpha=0.2, axis='y')
    
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/05b_subpop_car_avail.png", bbox_inches='tight')
    plt.close()
    print(f"   Saved: {VIS_DIR}/05b_subpop_car_avail.png")
    
    # ============================================================
    # 6. DEPARTURE TIME DISTRIBUTION
    # ============================================================
    print("6. Generating Departure Time Distribution...")
    
    def parse_time_to_hour(time_str):
        if not time_str:
            return None
        try:
            parts = time_str.split(':')
            return int(parts[0])
        except:
            return None
    
    fig, ax = plt.subplots(figsize=(14, 6))
    
    hours_by_mode = defaultdict(list)
    for t in trips:
        h = parse_time_to_hour(t['dep_time'])
        if h is not None and 0 <= h <= 30:
            hours_by_mode[t['mode']].append(h)
    
    hour_range = range(0, 31)
    
    for mode in ['car', 'pt', 'walk']:
        if mode in hours_by_mode:
            hour_counts = Counter(hours_by_mode[mode])
            counts = [hour_counts.get(h, 0) for h in hour_range]
            ax.plot(list(hour_range), counts, color=COLORS[mode], linewidth=2, 
                    label=f'{mode} ({sum(counts):,})', marker='o', markersize=3)
    
    ax.set_xlabel('Hour of Day', fontsize=12)
    ax.set_ylabel('Number of Departures', fontsize=12)
    ax.set_title('Departure Time Distribution by Mode - Jeonggwan v6 Baseline', 
                 fontsize=14, fontweight='bold')
    ax.legend(fontsize=11)
    ax.grid(True, alpha=0.3)
    ax.set_xlim(0, 30)
    
    # Mark peak hours
    ax.axvspan(7, 9, alpha=0.1, color='orange', label='AM Peak')
    ax.axvspan(17, 19, alpha=0.1, color='purple', label='PM Peak')
    
    plt.tight_layout()
    plt.savefig(f"{VIS_DIR}/06_departure_time.png", bbox_inches='tight')
    plt.close()
    print(f"   Saved: {VIS_DIR}/06_departure_time.png")
    
    # ============================================================
    # Summary stats
    # ============================================================
    summary = {
        'total_persons': total_persons,
        'total_trips': len(trips),
        'mode_share': {
            mode: sum(1 for t in trips if t['mode'] == mode) / len(trips)
            for mode in ['car', 'pt', 'walk']
        },
        'long_walks_10km': len(long_walks),
        'walk_distance_stats': {
            'median_km': round(np.median([t['distance']/1000 for t in trips if t['mode'] == 'walk']), 2),
            'mean_km': round(np.mean([t['distance']/1000 for t in trips if t['mode'] == 'walk']), 2),
            'max_km': round(max([t['distance']/1000 for t in trips if t['mode'] == 'walk']), 2),
        },
        'subpop_counts': {sp: dict(counts) for sp, counts in mode_by_subpop.items()}
    }
    
    with open(f"{VIS_DIR}/summary_stats.json", 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"\n   Summary saved: {VIS_DIR}/summary_stats.json")
    
    return summary


# ============================================================
# MAIN
# ============================================================
if __name__ == '__main__':
    if not HAS_MPL:
        print("ERROR: matplotlib is required. Install with: pip install matplotlib numpy")
        exit(1)
    
    print(f"\n{'='*60}")
    print("JEONGGWAN v6 BASELINE - VISUALIZATION SUITE")
    print(f"{'='*60}")
    print(f"Output dir: {OUTPUT_DIR}")
    print(f"Vis dir: {VIS_DIR}")
    print()
    
    # Simple CSV-based charts
    plot_mode_share_trend()
    plot_score_convergence()
    
    # Plans-based detailed analysis  
    summary = parse_plans_and_visualize()
    
    print(f"\n{'='*60}")
    print("ALL VISUALIZATIONS COMPLETE")
    print(f"{'='*60}")
    print(f"Files saved to: {VIS_DIR}/")
    print(f"  01_mode_share_trend.png")
    print(f"  01b_mode_share_pie.png")
    print(f"  02_score_convergence.png")
    print(f"  03_trip_distance_distribution.png")
    print(f"  04_walk_od_heatmap.png")
    print(f"  04b_walk_od_lines.png")
    print(f"  05_subpop_mode_share.png")
    print(f"  05b_subpop_car_avail.png")
    print(f"  06_departure_time.png")
    print(f"  summary_stats.json")
