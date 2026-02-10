"""Analyze Multi-Mode simulation results"""
import pandas as pd

base_path = 'output/jeonggwan-multimode'

print('=' * 60)
print('       MULTI-MODE (DRT + SAV) SIMULATION RESULTS')
print('=' * 60)

# Mode stats
modestats = pd.read_csv(f'{base_path}/null-multimode.modestats.csv', sep=';')
last = modestats.iloc[-1]
print('\n=== MODE SHARES (Iteration 50) ===')
for col in modestats.columns:
    if col != 'iteration':
        val = last[col]
        if isinstance(val, (int, float)) and val > 0:
            print(f'  {col}: {val*100:.1f}%')

# DRT legs
drt_legs = pd.read_csv(f'{base_path}/null-multimode.output_drt_legs_drt.csv', sep=';')
print(f'\n=== DRT STATISTICS (5 vehicles, 20 seats) ===')
print(f'  Total DRT trips: {len(drt_legs)}')
if 'waitTime' in drt_legs.columns:
    print(f'  Avg wait time: {drt_legs["waitTime"].mean():.1f}s ({drt_legs["waitTime"].mean()/60:.1f}min)')
    print(f'  Max wait time: {drt_legs["waitTime"].max():.1f}s ({drt_legs["waitTime"].max()/60:.1f}min)')

# SAV legs
sav_legs = pd.read_csv(f'{base_path}/null-multimode.output_drt_legs_sav.csv', sep=';')
print(f'\n=== SAV STATISTICS (10 vehicles, 4 seats) ===')
print(f'  Total SAV trips: {len(sav_legs)}')
if 'waitTime' in sav_legs.columns:
    print(f'  Avg wait time: {sav_legs["waitTime"].mean():.1f}s ({sav_legs["waitTime"].mean()/60:.1f}min)')
    print(f'  Max wait time: {sav_legs["waitTime"].max():.1f}s ({sav_legs["waitTime"].max()/60:.1f}min)')

# DRT rejections
try:
    drt_rej = pd.read_csv(f'{base_path}/null-multimode.output_drt_rejections_drt.csv', sep=';')
    print(f'\n=== REJECTIONS ===')
    print(f'  DRT rejections: {len(drt_rej) - 1}')  # minus header
except Exception as e:
    print(f'Cannot read rejections: {e}')

# Vehicle stats
print(f'\n=== DRT VEHICLE USAGE ===')
drt_veh_stats = pd.read_csv(f'{base_path}/null-multimode.drt_vehicle_stats_drt.csv', sep=';')
last_drt = drt_veh_stats.iloc[-1]
for col in ['vehicles', 'totalDistance', 'emptyRatio']:
    if col in drt_veh_stats.columns:
        print(f'  {col}: {last_drt[col]}')

print(f'\n=== SAV VEHICLE USAGE ===')
sav_veh_stats = pd.read_csv(f'{base_path}/null-multimode.drt_vehicle_stats_sav.csv', sep=';')
last_sav = sav_veh_stats.iloc[-1]
for col in ['vehicles', 'totalDistance', 'emptyRatio']:
    if col in sav_veh_stats.columns:
        print(f'  {col}: {last_sav[col]}')

print('\n' + '=' * 60)
