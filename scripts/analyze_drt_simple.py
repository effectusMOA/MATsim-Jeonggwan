"""Simple DRT analysis script - outputs to file"""
import pandas as pd

base_path = 'output/jeonggwan-drt'
output = []

# 1. DRT Legs
legs = pd.read_csv(f'{base_path}/null-drt.output_drt_legs_drt.csv', sep=';')
output.append('=== DRT LEG ANALYSIS ===')
output.append(f'Total DRT trips: {len(legs)}')
output.append(f'Columns: {list(legs.columns)}')

if 'waitTime' in legs.columns:
    output.append(f'Wait Time - Avg: {legs["waitTime"].mean():.1f}s, Min: {legs["waitTime"].min():.1f}s, Max: {legs["waitTime"].max():.1f}s')

if 'travelDistance' in legs.columns:
    output.append(f'Distance - Avg: {legs["travelDistance"].mean():.0f}m, Total: {legs["travelDistance"].sum()/1000:.1f}km')

# Hourly
if 'departureTime' in legs.columns:
    legs['hour'] = (legs['departureTime'] / 3600).astype(int)
    hourly = legs.groupby('hour').size()
    output.append('')
    output.append('Hourly usage:')
    for h, c in hourly.items():
        if 6 <= h <= 22:
            bar = '#' * (c // 3)
            output.append(f'  {h:02d}:00 - {c:3d} trips {bar}')

# Vehicle usage
if 'vehicle' in legs.columns:
    veh_usage = legs.groupby('vehicle').size().sort_values(ascending=False)
    output.append('')
    output.append('Vehicle usage (Top 10):')
    for veh, count in veh_usage.head(10).items():
        output.append(f'  {veh}: {count} trips')

# 2. Vehicle Stats
output.append('')
output.append('=== ITERATION STATISTICS ===')
veh_stats = pd.read_csv(f'{base_path}/null-drt.drt_vehicle_stats_drt.csv', sep=';')
output.append(f'Columns: {list(veh_stats.columns)}')
output.append('')
output.append('Final Iteration (50) Stats:')
last = veh_stats.iloc[-1]
for col in veh_stats.columns:
    if col not in ['runId', 'iteration']:
        output.append(f'  {col}: {last[col]:.2f}')

# 3. Vehicle Distance
output.append('')
output.append('=== VEHICLE DISTANCE STATS ===')
veh_dist = pd.read_csv(f'{base_path}/null-drt.output_vehicleDistanceStats_drt.csv', sep=';')
output.append(veh_dist.to_string())

# Write to file
with open('scripts/drt_analysis_result.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(output))

print('Analysis saved to scripts/drt_analysis_result.txt')
