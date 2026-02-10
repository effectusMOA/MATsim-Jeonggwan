"""
CORRECTED Mode Shift Analysis: it.0 vs it.90
Uses TRIP-LEVEL main_mode (not individual leg modes)
MATSim PT trips = walk(access) + pt + walk(egress), so we must classify
each activity-to-activity trip by its highest-priority mode.
"""
import gzip
import csv
import xml.etree.ElementTree as ET
import json
import os
from collections import defaultdict, Counter

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np

OUTPUT_DIR = "output/jeonggwan-v6-v6-baseline"
VIS_DIR = f"{OUTPUT_DIR}/visualizations"
os.makedirs(VIS_DIR, exist_ok=True)

plt.rcParams['font.family'] = ['Malgun Gothic', 'DejaVu Sans', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False
plt.rcParams['figure.dpi'] = 150

COLORS = {'car': '#E74C3C', 'pt': '#3498DB', 'walk': '#2ECC71'}

def get_trip_main_mode(leg_modes):
    """Determine main_mode from a list of leg modes in one trip.
    Priority: car > pt > walk (if any leg is pt, the trip is pt)"""
    modes = set(leg_modes)
    if 'car' in modes:
        return 'car'
    if 'pt' in modes:
        return 'pt'
    return 'walk'

# ============================================================
# 1. it.0: Read trip-level main_mode from trips.csv.gz
# ============================================================
print("1. Loading it.0 trip-level modes...")
it0_trips = defaultdict(list)  # person -> [main_mode per trip]

with gzip.open(f"{OUTPUT_DIR}/ITERS/it.0/0.trips.csv.gz", 'rt') as f:
    reader = csv.DictReader(f, delimiter=';')
    for row in reader:
        it0_trips[row['person']].append(row['main_mode'])

it0_counts = Counter()
for person, modes in it0_trips.items():
    for m in modes:
        it0_counts[m] += 1
print(f"   it.0: {len(it0_trips)} persons, {sum(it0_counts.values())} trips")
print(f"   Modes: {dict(it0_counts)}")

# ============================================================
# 2. it.90: Parse plans, group legs into trips, determine main_mode
# ============================================================
print("2. Loading it.90 trip-level modes from plans...")
it90_trips = defaultdict(list)  # person -> [main_mode per trip]

with gzip.open(f"{OUTPUT_DIR}/ITERS/it.90/90.plans.xml.gz", 'rb') as f:
    context = ET.iterparse(f, events=['start', 'end'])
    current_person = None
    current_plan_selected = False
    current_trip_legs = []  # legs in current trip (between activities)
    in_trip = False
    
    for event, elem in context:
        if event == 'start' and elem.tag == 'person':
            current_person = elem.get('id')
            
        elif event == 'start' and elem.tag == 'plan':
            current_plan_selected = elem.get('selected') == 'yes'
            current_trip_legs = []
            in_trip = False
            
        elif event == 'start' and elem.tag == 'activity' and current_plan_selected:
            # An activity marks the end of a trip (if we were in one)
            if in_trip and current_trip_legs:
                main_mode = get_trip_main_mode(current_trip_legs)
                it90_trips[current_person].append(main_mode)
                current_trip_legs = []
            in_trip = True  # Next legs form a new trip
                
        elif event == 'start' and elem.tag == 'leg' and current_plan_selected:
            current_trip_legs.append(elem.get('mode'))
            
        elif event == 'end' and elem.tag == 'person':
            current_person = None
            elem.clear()

it90_counts = Counter()
for person, modes in it90_trips.items():
    for m in modes:
        it90_counts[m] += 1
print(f"   it.90: {len(it90_trips)} persons, {sum(it90_counts.values())} trips")
print(f"   Modes: {dict(it90_counts)}")

# ============================================================
# 3. Build trip-level mode shift matrix
# ============================================================
print("\n3. Building trip-level mode shift...")
mode_list = ['car', 'pt', 'walk']

# Per-trip comparison (match by person + trip_number)
shift_matrix = Counter()
total_matched = 0

common_persons = set(it0_trips.keys()) & set(it90_trips.keys())
print(f"   Common persons: {len(common_persons)}")

for person in common_persons:
    trips_0 = it0_trips[person]
    trips_90 = it90_trips[person]
    # Match trips by index (trip_number)
    for i in range(min(len(trips_0), len(trips_90))):
        if trips_0[i] in mode_list and trips_90[i] in mode_list:
            shift_matrix[(trips_0[i], trips_90[i])] += 1
            total_matched += 1

print(f"   Matched trips: {total_matched}")

# Print matrix
print(f"\n   Trip-Level Mode Shift Matrix (it.0 → it.90):")
print(f"   {'':>10}", end='')
for m in mode_list:
    print(f"{m:>10}", end='')
print(f"{'Total':>10}{'Retention':>12}")

for init_m in mode_list:
    print(f"   {init_m:>10}", end='')
    row_total = 0
    same = 0
    for final_m in mode_list:
        count = shift_matrix.get((init_m, final_m), 0)
        print(f"{count:>10}", end='')
        row_total += count
        if init_m == final_m:
            same = count
    retention = same/row_total*100 if row_total > 0 else 0
    print(f"{row_total:>10}{retention:>11.1f}%")

# ============================================================
# 4. Visualize: Heatmap Matrix
# ============================================================
print("\n4. Generating corrected heatmap...")

matrix_pct = np.zeros((3, 3))
for i, init_m in enumerate(mode_list):
    row_total = sum(shift_matrix.get((init_m, fm), 0) for fm in mode_list)
    for j, final_m in enumerate(mode_list):
        count = shift_matrix.get((init_m, final_m), 0)
        matrix_pct[i, j] = count / row_total * 100 if row_total > 0 else 0

fig, ax = plt.subplots(figsize=(9, 7.5))
im = ax.imshow(matrix_pct, cmap='YlOrRd', aspect='auto', vmin=0, vmax=100)

for i in range(3):
    for j in range(3):
        count = shift_matrix.get((mode_list[i], mode_list[j]), 0)
        pct = matrix_pct[i, j]
        color = 'white' if pct > 50 else 'black'
        ax.text(j, i, f'{pct:.1f}%\n({count:,})',
                ha='center', va='center', fontsize=12, fontweight='bold', color=color)

ax.set_xticks(range(3))
ax.set_yticks(range(3))
ax.set_xticklabels([m.upper() for m in mode_list], fontsize=13)
ax.set_yticklabels([m.upper() for m in mode_list], fontsize=13)
ax.set_xlabel('Final Mode (it.90)', fontsize=13, fontweight='bold')
ax.set_ylabel('Initial Mode (it.0)', fontsize=13, fontweight='bold')
ax.set_title('Trip-Level Mode Shift Matrix (it.0 → it.90)\nJeonggwan v6 Baseline', 
             fontsize=14, fontweight='bold')
plt.colorbar(im, label='Percentage (%)')
plt.tight_layout()
plt.savefig(f"{VIS_DIR}/07_mode_shift_matrix.png", bbox_inches='tight')
plt.close()
print(f"   Saved: {VIS_DIR}/07_mode_shift_matrix.png")

# ============================================================
# 5. Visualize: Flow Diagram 
# ============================================================
print("5. Generating corrected flow diagram...")

fig, ax = plt.subplots(figsize=(14, 8))
left_x, right_x, bar_width = 0.15, 0.85, 0.08

init_totals = {m: sum(shift_matrix.get((m, fm), 0) for fm in mode_list) for m in mode_list}
final_totals = {m: sum(shift_matrix.get((im, m), 0) for im in mode_list) for m in mode_list}
grand_total = sum(init_totals.values())

def get_positions(totals):
    positions = {}
    current_y = 0
    gap = 0.03
    for m in mode_list:
        h = totals[m] / grand_total if grand_total > 0 else 0
        positions[m] = {'bottom': current_y, 'height': h, 'center': current_y + h/2}
        current_y += h + gap
    return positions

left_pos = get_positions(init_totals)
right_pos = get_positions(final_totals)

# Draw bars
for m in mode_list:
    for pos, x_pos, ha, sign in [(left_pos, left_x, 'right', -1), 
                                   (right_pos, right_x, 'left', 1)]:
        p = pos[m]
        rect = plt.Rectangle((x_pos - bar_width/2, p['bottom']), bar_width, p['height'],
                              facecolor=COLORS[m], edgecolor='white', linewidth=2, zorder=3)
        ax.add_patch(rect)
        totals = init_totals if sign == -1 else final_totals
        pct = totals[m] / grand_total * 100 if grand_total > 0 else 0
        text_x = x_pos + sign * (bar_width/2 + 0.02)
        ax.text(text_x, p['center'],
                f"{m.upper()}\n{totals[m]:,}\n({pct:.1f}%)",
                ha=ha, va='center', fontsize=11, fontweight='bold')

# Draw flows
left_offsets = {m: 0 for m in mode_list}
right_offsets = {m: 0 for m in mode_list}

for init_m in mode_list:
    for final_m in mode_list:
        count = shift_matrix.get((init_m, final_m), 0)
        if count == 0:
            continue
        
        flow_h = count / grand_total
        
        y_start_bottom = left_pos[init_m]['bottom'] + left_offsets[init_m]
        y_start_top = y_start_bottom + flow_h
        left_offsets[init_m] += flow_h
        
        y_end_bottom = right_pos[final_m]['bottom'] + right_offsets[final_m]
        y_end_top = y_end_bottom + flow_h
        right_offsets[final_m] += flow_h
        
        x_pts = np.linspace(left_x + bar_width/2, right_x - bar_width/2, 100)
        t = (x_pts - x_pts[0]) / (x_pts[-1] - x_pts[0])
        smooth_t = 3*t**2 - 2*t**3
        
        y_bottom = y_start_bottom + smooth_t * (y_end_bottom - y_start_bottom)
        y_top = y_start_top + smooth_t * (y_end_top - y_start_top)
        
        color = COLORS[init_m] if init_m == final_m else COLORS[final_m]
        alpha = 0.4 if init_m == final_m else 0.25
        
        ax.fill_between(x_pts, y_bottom, y_top, color=color, alpha=alpha, zorder=1)
        
        # Label flows > 3%
        if count / grand_total > 0.03:
            mid_y = (y_start_bottom + y_start_top + y_end_bottom + y_end_top) / 4
            pct = count / grand_total * 100
            ax.text(0.5, mid_y, f'{count:,}\n({pct:.0f}%)', ha='center', va='center',
                    fontsize=9, fontweight='bold', alpha=0.7)

max_y = max(
    left_pos[mode_list[-1]]['bottom'] + left_pos[mode_list[-1]]['height'],
    right_pos[mode_list[-1]]['bottom'] + right_pos[mode_list[-1]]['height']
)
ax.set_xlim(0, 1)
ax.set_ylim(-0.05, max_y + 0.08)
ax.axis('off')

ax.text(left_x, -0.04, 'Initial (it.0)', ha='center', fontsize=13, fontweight='bold')
ax.text(right_x, -0.04, 'Final (it.90)', ha='center', fontsize=13, fontweight='bold')
ax.set_title('Trip-Level Mode Shift Flow: it.0 → it.90\nJeonggwan v6 Baseline (Corrected)',
             fontsize=14, fontweight='bold', pad=20)

plt.tight_layout()
plt.savefig(f"{VIS_DIR}/07b_mode_shift_flow.png", bbox_inches='tight')
plt.close()
print(f"   Saved: {VIS_DIR}/07b_mode_shift_flow.png")

# ============================================================
# 6. Summary
# ============================================================
print("\n6. Summary:")
stayed = sum(shift_matrix.get((m, m), 0) for m in mode_list)
changed = total_matched - stayed
print(f"   Total matched trips: {total_matched:,}")
print(f"   Stayed same mode: {stayed:,} ({stayed/total_matched*100:.1f}%)")
print(f"   Changed mode: {changed:,} ({changed/total_matched*100:.1f}%)")

print(f"\n   Key shifts:")
shifts = []
for init_m in mode_list:
    for final_m in mode_list:
        if init_m != final_m:
            count = shift_matrix.get((init_m, final_m), 0)
            if count > 0:
                shifts.append((init_m, final_m, count))
shifts.sort(key=lambda x: x[2], reverse=True)
for init_m, final_m, count in shifts:
    pct = count / total_matched * 100
    print(f"   {init_m.upper()} → {final_m.upper()}: {count:,} ({pct:.1f}%)")

print(f"\n   Mode retention rates:")
for m in mode_list:
    total_init = sum(shift_matrix.get((m, fm), 0) for fm in mode_list)
    same = shift_matrix.get((m, m), 0)
    if total_init > 0:
        print(f"   {m.upper()}: {same:,}/{total_init:,} = {same/total_init*100:.1f}%")

results = {
    'total_matched_trips': total_matched,
    'stayed_same': stayed,
    'changed': changed,
    'it0_trip_counts': dict(it0_counts),
    'it90_trip_counts': dict(it90_counts),
    'shift_matrix': {f"{im}->{fm}": shift_matrix.get((im, fm), 0) 
                     for im in mode_list for fm in mode_list}
}
with open(f"{VIS_DIR}/mode_shift_data.json", 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)
print(f"\n   Saved: {VIS_DIR}/mode_shift_data.json")
