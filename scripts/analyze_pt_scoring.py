"""
Analyze PT vs Walk scoring in MATSim
Check the scoring parameters and calculate why Walk might be preferred
"""
import xml.etree.ElementTree as ET
import json

print("="*60)
print("PT vs WALK SCORING ANALYSIS")
print("="*60)

# Load config
print("\n1. Loading scoring parameters from config...")
tree = ET.parse('input/jeonggwan-config-v6.xml')
root = tree.getroot()

scoring_params = {}
mode_params = {}

for module in root.findall('module'):
    if module.get('name') == 'scoring':
        for param in module.findall('param'):
            scoring_params[param.get('name')] = param.get('value')
        
        for pset in module.findall('parameterset'):
            if pset.get('type') == 'scoringParameters':
                subpop = None
                for p in pset.findall('param'):
                    if p.get('name') == 'subpopulation':
                        subpop = p.get('value')
                
                for mpset in pset.findall('parameterset'):
                    if mpset.get('type') == 'modeParams':
                        mode = None
                        params = {}
                        for p in mpset.findall('param'):
                            if p.get('name') == 'mode':
                                mode = p.get('value')
                            else:
                                params[p.get('name')] = p.get('value')
                        if mode:
                            mode_params[mode] = params

print(f"   Found parameters for modes: {list(mode_params.keys())}")

# Check transitRouter settings
transit_router_params = {}
for module in root.findall('module'):
    if module.get('name') == 'transitRouter':
        for param in module.findall('param'):
            transit_router_params[param.get('name')] = param.get('value')

print(f"\n2. Transit Router Parameters:")
for k, v in transit_router_params.items():
    print(f"   {k}: {v}")

# Calculate trip utilities for a sample 20km trip
print("\n3. Scoring Comparison for 20km Trip:")
print("="*60)

TRIP_DISTANCE = 20000  # 20km in meters
WALK_SPEED = 0.833  # m/s (3 km/h)
PT_AVG_SPEED = 6.0    # m/s (~22 km/h including waiting)
CAR_SPEED = 10.0   # m/s (~36 km/h in urban)

# Walk calculation
walk_params = mode_params.get('walk', {})
walk_marginal_dist = float(walk_params.get('marginalUtilityOfDistance_util_m', '-0.0005'))
walk_constant = float(walk_params.get('constant', '0'))
walk_time = TRIP_DISTANCE / WALK_SPEED  # seconds

# Assuming marginalUtilityOfTraveling_util_hr = -6 (typical)
walk_travel_util = -6.0 * (walk_time / 3600)
walk_dist_util = walk_marginal_dist * TRIP_DISTANCE
walk_total = walk_constant + walk_travel_util + walk_dist_util

print(f"\nWALK (20km):")
print(f"   Travel time: {walk_time/60:.0f} min ({walk_time/3600:.1f} hr)")
print(f"   Constant: {walk_constant}")
print(f"   Time utility: {walk_travel_util:.2f} (assuming -6/hr)")
print(f"   Distance utility: {walk_dist_util:.2f}")
print(f"   TOTAL: {walk_total:.2f}")

# PT calculation
pt_params = mode_params.get('pt', {})
pt_constant = float(pt_params.get('constant', '-1.5'))
pt_daily_cost = float(pt_params.get('dailyMonetaryConstant', '-1.0'))
pt_time = TRIP_DISTANCE / PT_AVG_SPEED

# PT typically involves waiting + access/egress walks
pt_wait_time = 10 * 60  # 10 min average wait
pt_access_time = 5 * 60  # 5 min walk to stop
pt_egress_time = 5 * 60  # 5 min walk from stop
pt_total_time = pt_time + pt_wait_time + pt_access_time + pt_egress_time

pt_travel_util = -6.0 * (pt_total_time / 3600)
pt_total = pt_constant + pt_travel_util + pt_daily_cost

print(f"\nPT (20km):")
print(f"   In-vehicle time: {pt_time/60:.0f} min")
print(f"   Wait + access/egress: {(pt_wait_time + pt_access_time + pt_egress_time)/60:.0f} min")
print(f"   Total time: {pt_total_time/60:.0f} min ({pt_total_time/3600:.1f} hr)")
print(f"   Constant: {pt_constant}")
print(f"   Time utility: {pt_travel_util:.2f}")
print(f"   Daily cost: {pt_daily_cost}")
print(f"   TOTAL: {pt_total:.2f}")

# Car calculation
car_params = mode_params.get('car', {})
car_constant = float(car_params.get('constant', '0'))
car_daily_cost = float(car_params.get('dailyMonetaryConstant', '-3.5'))
car_dist_cost = float(car_params.get('monetaryDistanceRate', '-0.0002'))
car_time = TRIP_DISTANCE / CAR_SPEED

car_travel_util = -6.0 * (car_time / 3600)
car_dist_util = car_dist_cost * TRIP_DISTANCE
car_total = car_constant + car_travel_util + car_daily_cost + car_dist_util

print(f"\nCAR (20km):")
print(f"   Travel time: {car_time/60:.0f} min")
print(f"   Constant: {car_constant}")
print(f"   Time utility: {car_travel_util:.2f}")
print(f"   Daily cost: {car_daily_cost}")
print(f"   Distance cost: {car_dist_util:.2f}")
print(f"   TOTAL: {car_total:.2f}")

print("\n" + "="*60)
print("COMPARISON SUMMARY:")
print("="*60)
print(f"   Walk: {walk_total:.2f}")
print(f"   PT:   {pt_total:.2f}")
print(f"   Car:  {car_total:.2f}")

if walk_total > pt_total:
    print(f"\n   >> Walk has HIGHER utility than PT by {walk_total - pt_total:.2f}")
    print(f"   >> This explains why agents prefer walking!")
else:
    print(f"\n   >> PT has higher utility than Walk by {pt_total - walk_total:.2f}")

# BUT the key issue: if PT route doesn't exist, PT utility = -infinity
print("\n⚠️ CRITICAL NOTE:")
print("   If NO PT route is found, MATSim assigns PT utility = -∞")
print("   Walk will ALWAYS be chosen when PT is unavailable!")

# Save results
results = {
    'walk': {'time_min': walk_time/60, 'utility': walk_total},
    'pt': {'time_min': pt_total_time/60, 'utility': pt_total},
    'car': {'time_min': car_time/60, 'utility': car_total},
    'walk_params': walk_params,
    'pt_params': pt_params,
    'transit_router_params': transit_router_params
}

with open('output/scoring_analysis.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, indent=2, ensure_ascii=False)

print(f"\nSaved to output/scoring_analysis.json")
