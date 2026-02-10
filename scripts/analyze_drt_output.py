"""
DRT 시뮬레이션 결과 분석 스크립트
세 가지 CSV 파일을 분석합니다:
1. output_drt_legs_drt.csv - 모든 DRT 이용 상세 내역
2. output_vehicleDistanceStats_drt.csv - 차량별 주행 거리 통계
3. drt_vehicle_stats_drt.csv - 차량별 상세 통계
"""
import pandas as pd
import numpy as np

base_path = 'output/jeonggwan-drt'

print('=' * 70)
print('              DRT SIMULATION RESULT ANALYSIS REPORT')
print('=' * 70)

# ============================================================
# 1. DRT Legs (이용 상세 내역)
# ============================================================
print('\n\n[1] DRT Leg Details Analysis')
print('-' * 70)
legs = pd.read_csv(f'{base_path}/null-drt.output_drt_legs_drt.csv', sep=';')

print(f'Total DRT trips: {len(legs)}')
print(f'\nColumns:')
for col in legs.columns:
    print(f'   - {col}')

print(f'\n=== Key Statistics ===')
if 'waitTime' in legs.columns:
    print(f'\n[Wait Time (seconds)]')
    print(f'   Average: {legs["waitTime"].mean():.1f}s ({legs["waitTime"].mean()/60:.1f}min)')
    print(f'   Min: {legs["waitTime"].min():.1f}s')
    print(f'   Max: {legs["waitTime"].max():.1f}s')
    print(f'   Median: {legs["waitTime"].median():.1f}s')

if 'arrivalTime' in legs.columns and 'departureTime' in legs.columns:
    legs['rideTime'] = legs['arrivalTime'] - legs['departureTime']
    print(f'\n[Ride Time (seconds)]')
    print(f'   Average: {legs["rideTime"].mean():.1f}s ({legs["rideTime"].mean()/60:.1f}min)')
    print(f'   Min: {legs["rideTime"].min():.1f}s')
    print(f'   Max: {legs["rideTime"].max():.1f}s')

if 'travelDistance' in legs.columns:
    print(f'\n[Travel Distance (m)]')
    print(f'   Average: {legs["travelDistance"].mean():.0f}m ({legs["travelDistance"].mean()/1000:.1f}km)')
    print(f'   Min: {legs["travelDistance"].min():.0f}m')
    print(f'   Max: {legs["travelDistance"].max():.0f}m')
    print(f'   Total: {legs["travelDistance"].sum()/1000:.1f}km')

# 시간대별 분석
if 'departureTime' in legs.columns:
    legs['hour'] = (legs['departureTime'] / 3600).astype(int)
    hourly = legs.groupby('hour').size()
    print(f'\n[Hourly DRT Usage]')
    for hour, count in hourly.items():
        if 6 <= hour <= 22:  # 운영 시간대만
            bar = '#' * (count // 3) if count > 0 else ''
            print(f'   {hour:02d}:00 - {hour+1:02d}:00 : {count:3d} trips {bar}')

# 차량별 이용 현황
if 'vehicle' in legs.columns:
    veh_usage = legs.groupby('vehicle').size().sort_values(ascending=False)
    print(f'\n[Vehicle Usage (Top 10)]')
    for veh, count in veh_usage.head(10).items():
        print(f'   {veh}: {count} trips')

# ============================================================
# 2. Vehicle Distance Stats
# ============================================================
print('\n\n[2] 차량별 주행 거리 통계')
print('-' * 70)
veh_dist = pd.read_csv(f'{base_path}/null-drt.output_vehicleDistanceStats_drt.csv', sep=';')
print(veh_dist.to_string())

# ============================================================
# 3. Vehicle Stats (Iteration별)
# ============================================================
print('\n\n[3] 반복별 DRT 시스템 통계')
print('-' * 70)
veh_stats = pd.read_csv(f'{base_path}/null-drt.drt_vehicle_stats_drt.csv', sep=';')
print(f'\n📋 데이터 컬럼:')
for col in veh_stats.columns:
    print(f'   - {col}')

# 첫 번째와 마지막 반복 비교
print(f'\n📈 시뮬레이션 수렴 분석 (첫 반복 vs 마지막 반복):')
first = veh_stats.iloc[0]
last = veh_stats.iloc[-1]

metrics = [
    ('rides', 'DRT 이용 건수'),
    ('wait_average', '평균 대기시간 (초)'),
    ('wait_p95', '95% 대기시간 (초)'),
    ('wait_max', '최대 대기시간 (초)'),
]

for metric, name in metrics:
    if metric in veh_stats.columns:
        print(f'   {name}:')
        print(f'      1회차: {first[metric]:.1f}')
        print(f'     50회차: {last[metric]:.1f}')
        change = ((last[metric] - first[metric]) / first[metric] * 100) if first[metric] != 0 else 0
        print(f'      변화율: {change:+.1f}%')

# 마지막 반복의 주요 지표
print(f'\n📊 최종 반복 (Iteration 50) 주요 지표:')
for col in veh_stats.columns:
    if col not in ['runId', 'iteration']:
        print(f'   {col}: {last[col]:.2f}')

print('\n' + '=' * 70)
print('                      분석 완료')
print('=' * 70)
