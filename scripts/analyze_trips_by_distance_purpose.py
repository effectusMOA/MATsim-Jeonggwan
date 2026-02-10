"""
Analyze mode choice by trip distance and purpose - writes to file
"""
import pandas as pd
import gzip

base_path = 'output/jeonggwan-multimode'
output_file = 'scripts/trip_analysis_result.txt'

# Read trips data
with gzip.open(f'{base_path}/null-multimode.output_trips.csv.gz', 'rt') as f:
    trips = pd.read_csv(f, sep=';')

results = []
results.append('=' * 70)
results.append('        MODE CHOICE BY DISTANCE AND PURPOSE ANALYSIS')
results.append('=' * 70)

# Distance classification
def classify_distance(dist_m):
    if pd.isna(dist_m):
        return 'Unknown'
    if dist_m < 2000:
        return 'Short (<2km)'
    elif dist_m < 10000:
        return 'Medium (2-10km)'
    else:
        return 'Long (>10km)'

# Purpose classification
def classify_purpose(dest_act):
    if pd.isna(dest_act):
        return 'Unknown'
    dest_act = str(dest_act).lower()
    if 'work' in dest_act or 'education' in dest_act:
        return 'Mandatory'
    elif 'home' in dest_act:
        return 'Home Return'
    else:
        return 'Leisure'

# Apply classifications
trips['distance_class'] = trips['traveled_distance'].apply(classify_distance)
trips['purpose_class'] = trips['end_activity_type'].apply(classify_purpose)

# Analysis by distance
results.append('\n=== MODE SHARE BY DISTANCE ===')
for dist_class in ['Short (<2km)', 'Medium (2-10km)', 'Long (>10km)']:
    subset = trips[trips['distance_class'] == dist_class]
    if len(subset) > 0:
        results.append(f'\n[{dist_class}] Total trips: {len(subset)}')
        mode_counts = subset['main_mode'].value_counts()
        for mode, count in mode_counts.items():
            pct = count / len(subset) * 100
            results.append(f'  {mode}: {count} ({pct:.1f}%)')

# Analysis by purpose
results.append('\n\n=== MODE SHARE BY PURPOSE ===')
for purpose in ['Mandatory', 'Leisure', 'Home Return']:
    subset = trips[trips['purpose_class'] == purpose]
    if len(subset) > 0:
        results.append(f'\n[{purpose}] Total trips: {len(subset)}')
        mode_counts = subset['main_mode'].value_counts()
        for mode, count in mode_counts.items():
            pct = count / len(subset) * 100
            results.append(f'  {mode}: {count} ({pct:.1f}%)')

# Cross-tabulation
results.append('\n\n=== CROSS-TABULATION: MODE BY DISTANCE x PURPOSE ===')
for purpose in ['Mandatory', 'Leisure']:
    results.append(f'\n[{purpose} Trips]')
    purpose_subset = trips[trips['purpose_class'] == purpose]
    for dist_class in ['Short (<2km)', 'Medium (2-10km)', 'Long (>10km)']:
        subset = purpose_subset[purpose_subset['distance_class'] == dist_class]
        if len(subset) > 0:
            results.append(f'  {dist_class}: {len(subset)} trips')
            mode_counts = subset['main_mode'].value_counts()
            for mode, count in mode_counts.head(3).items():
                pct = count / len(subset) * 100
                results.append(f'    - {mode}: {pct:.1f}%')

results.append('\n' + '=' * 70)

# Write to file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print(f'Results written to {output_file}')
