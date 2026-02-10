"""
DRT Stop Usage Analysis - Analyze which stops are most popular
Also analyzes: sharing metrics, vehicle efficiency, wait times
"""
import pandas as pd

base_path = 'output/jeonggwan-multimode'
output_file = 'scripts/drt_stop_analysis_result.txt'

results = []
results.append('=' * 70)
results.append('           DRT DETAILED ANALYSIS REPORT')
results.append('=' * 70)

# ============================================================
# 1. STOP USAGE ANALYSIS (Boardings & Alightments)
# ============================================================
results.append('\n\n=== 1. DRT STOP USAGE ANALYSIS ===')

try:
    boardings = pd.read_csv(f'{base_path}/null-multimode.output_drt_boardings_drt.csv', sep=';')
    alightments = pd.read_csv(f'{base_path}/null-multimode.output_drt_alightments_drt.csv', sep=';')
    
    results.append(f'\nTotal boarding records: {len(boardings)}')
    results.append(f'Total alightment records: {len(alightments)}')
    results.append(f'\nColumns in boardings: {list(boardings.columns)}')
    
    # Find stop/link column
    stop_col = None
    for col in boardings.columns:
        if 'stop' in col.lower() or 'link' in col.lower() or 'facility' in col.lower():
            stop_col = col
            break
    
    if stop_col:
        results.append(f'\n[Top 10 Boarding Stops]')
        top_boardings = boardings[stop_col].value_counts().head(10)
        for stop, count in top_boardings.items():
            results.append(f'  {stop}: {count} boardings')
        
        results.append(f'\n[Top 10 Alightment Stops]')
        alightment_col = stop_col if stop_col in alightments.columns else alightments.columns[0]
        top_alightments = alightments[alightment_col].value_counts().head(10) if alightment_col in alightments.columns else pd.Series()
        for stop, count in top_alightments.items():
            results.append(f'  {stop}: {count} alightments')
    else:
        results.append('Stop column not found in data')
        results.append(f'Available columns: {list(boardings.columns)}')
except Exception as e:
    results.append(f'Error reading boarding data: {e}')

# ============================================================
# 2. SHARING METRICS (Pooling Analysis)
# ============================================================
results.append('\n\n=== 2. SHARING/POOLING METRICS ===')

try:
    sharing = pd.read_csv(f'{base_path}/null-multimode.drt_sharing_metrics_drt.csv', sep=';')
    last = sharing.iloc[-1]
    results.append(f'\nFinal Iteration Sharing Metrics:')
    for col in sharing.columns:
        if col not in ['runId', 'iteration']:
            results.append(f'  {col}: {last[col]}')
except Exception as e:
    results.append(f'Error: {e}')

# ============================================================
# 3. VEHICLE EFFICIENCY
# ============================================================
results.append('\n\n=== 3. VEHICLE EFFICIENCY ===')

try:
    veh_dist = pd.read_csv(f'{base_path}/null-multimode.output_vehicleDistanceStats_drt.csv', sep=';')
    results.append(f'\n[Vehicle Distance Stats]')
    for col in veh_dist.columns:
        results.append(f'  {col}: {veh_dist[col].values[0]}')
except Exception as e:
    results.append(f'Error: {e}')

# ============================================================
# 4. WAIT TIME DISTRIBUTION
# ============================================================
results.append('\n\n=== 4. WAIT TIME DISTRIBUTION ===')

try:
    wait_stats = pd.read_csv(f'{base_path}/null-multimode.output_waitStats_drt.csv', sep=';')
    results.append(f'\n[Wait Time by Time Bin]')
    for _, row in wait_stats.iterrows():
        results.append(f'  {row.to_dict()}')
except Exception as e:
    results.append(f'Error: {e}')

# ============================================================
# 5. DRT LEGS ANALYSIS (Hourly)
# ============================================================
results.append('\n\n=== 5. HOURLY DRT USAGE ===')

try:
    legs = pd.read_csv(f'{base_path}/null-multimode.output_drt_legs_drt.csv', sep=';')
    if 'departureTime' in legs.columns:
        legs['hour'] = (legs['departureTime'] / 3600).astype(int)
        hourly = legs.groupby('hour').size()
        results.append(f'\n[DRT Trips by Hour]')
        for hour, count in hourly.items():
            if 6 <= hour <= 22:
                bar = '#' * (count // 2)
                results.append(f'  {hour:02d}:00 - {count:3d} trips {bar}')
except Exception as e:
    results.append(f'Error: {e}')

results.append('\n' + '=' * 70)

# Write to file
with open(output_file, 'w', encoding='utf-8') as f:
    f.write('\n'.join(results))

print(f'Analysis saved to {output_file}')
