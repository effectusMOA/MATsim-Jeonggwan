"""
PT Agent Score Analysis
Examines individual agents who use PT to understand scoring dynamics.
Compares:
  - Agents still using PT (it.90 selected plan)
  - Their alternative plans (non-selected) and scores
  - PT vs Walk trip utility breakdown
"""
import gzip
import xml.etree.ElementTree as ET
import math
import json
from collections import defaultdict

OUTPUT_DIR = "output/jeonggwan-v6-v6-baseline"
PLANS_FILE = f"{OUTPUT_DIR}/ITERS/it.90/90.plans.xml.gz"

print("="*70)
print("PT AGENT SCORE ANALYSIS (it.90)")
print("="*70)

# Parse all plans for agents who have PT in any plan
print("\nParsing plans file...")

agents_data = {}  # person_id -> { attrs, plans: [{selected, score, trips: [...]}] }
MAX_AGENTS = 200000  # process all

person_count = 0

with gzip.open(PLANS_FILE, 'rb') as f:
    context = ET.iterparse(f, events=['start', 'end'])
    current_person = None
    person_attrs = {}
    current_plans = []
    current_plan = None
    current_activities = []
    current_legs = []
    
    for event, elem in context:
        if event == 'start' and elem.tag == 'person':
            current_person = elem.get('id')
            person_attrs = {}
            current_plans = []
            person_count += 1
            
        elif event == 'start' and elem.tag == 'attribute' and current_person and not current_plan:
            name = elem.get('name')
            if name and elem.text:
                person_attrs[name] = elem.text
                
        elif event == 'start' and elem.tag == 'plan':
            current_plan = {
                'selected': elem.get('selected') == 'yes',
                'score': float(elem.get('score', 'NaN')) if elem.get('score') else None,
            }
            current_activities = []
            current_legs = []
            
        elif event == 'start' and elem.tag == 'activity' and current_plan:
            current_activities.append({
                'type': elem.get('type'),
                'x': float(elem.get('x', 0)),
                'y': float(elem.get('y', 0)),
                'end_time': elem.get('end_time'),
            })
            
        elif event == 'start' and elem.tag == 'leg' and current_plan:
            current_legs.append({
                'mode': elem.get('mode'),
                'dep_time': elem.get('dep_time'),
                'trav_time': elem.get('trav_time'),
            })
            
        elif event == 'end' and elem.tag == 'plan':
            if current_plan:
                # Build trips from activities and legs
                trips = []
                trip_legs = []
                for i, leg in enumerate(current_legs):
                    trip_legs.append(leg)
                    # A trip ends at the next activity (non-pt interaction)
                    next_act_idx = i + 1
                    if next_act_idx < len(current_activities):
                        next_act = current_activities[next_act_idx]
                        if next_act['type'] != 'pt interaction':
                            # Trip complete
                            modes_in_trip = [l['mode'] for l in trip_legs]
                            main_mode = 'car' if 'car' in modes_in_trip else \
                                       'pt' if 'pt' in modes_in_trip else 'walk'
                            
                            origin = current_activities[max(0, next_act_idx - len(trip_legs))]
                            dest = next_act
                            dx = origin['x'] - dest['x']
                            dy = origin['y'] - dest['y']
                            dist = math.sqrt(dx*dx + dy*dy)
                            
                            trips.append({
                                'main_mode': main_mode,
                                'legs': trip_legs.copy(),
                                'origin_type': origin['type'],
                                'dest_type': dest['type'],
                                'distance_km': round(dist/1000, 2),
                                'dep_time': trip_legs[0]['dep_time'],
                            })
                            trip_legs = []
                
                current_plan['trips'] = trips
                current_plan['activities'] = current_activities
                current_plans.append(current_plan)
                current_plan = None
                
        elif event == 'end' and elem.tag == 'person':
            # Check if this person has PT in any plan
            has_pt = False
            for plan in current_plans:
                for trip in plan.get('trips', []):
                    if trip['main_mode'] == 'pt':
                        has_pt = True
                        break
                if has_pt:
                    break
            
            if has_pt:
                agents_data[current_person] = {
                    'attrs': person_attrs,
                    'plans': current_plans,
                }
            
            current_person = None
            elem.clear()

print(f"Total persons: {person_count}")
print(f"Persons with PT in any plan: {len(agents_data)}")

# ============================================================
# Categorize agents
# ============================================================
pt_selected = {}   # PT is in selected plan
pt_unselected = {} # PT only in non-selected plans (rejected)

for pid, data in agents_data.items():
    selected_plan = None
    for plan in data['plans']:
        if plan['selected']:
            selected_plan = plan
            break
    
    if not selected_plan:
        continue
        
    selected_modes = set(t['main_mode'] for t in selected_plan.get('trips', []))
    
    if 'pt' in selected_modes:
        pt_selected[pid] = data
    else:
        pt_unselected[pid] = data

print(f"\nPT in SELECTED plan: {len(pt_selected)} agents")
print(f"PT only in REJECTED plans: {len(pt_unselected)} agents")

# ============================================================
# Detailed analysis of sample agents
# ============================================================
def print_agent(pid, data, label):
    print(f"\n{'='*60}")
    print(f" {label}: Agent {pid}")
    print(f"{'='*60}")
    attrs = data['attrs']
    print(f"  Subpop: {attrs.get('subpopulation','?')}, "
          f"CarAvail: {attrs.get('carAvail','?')}")
    
    for i, plan in enumerate(data['plans']):
        sel = "★ SELECTED" if plan['selected'] else "  (rejected)"
        score = plan.get('score')
        score_str = f"{score:.2f}" if score is not None else "N/A"
        print(f"\n  Plan {i+1} {sel}  Score: {score_str}")
        
        for j, trip in enumerate(plan.get('trips', [])):
            leg_modes = [l['mode'] for l in trip['legs']]
            leg_str = " → ".join(leg_modes)
            print(f"    Trip {j+1}: {trip['origin_type']} → {trip['dest_type']}")
            print(f"      Main mode: {trip['main_mode'].upper()}, "
                  f"Distance: {trip['distance_km']:.1f}km, "
                  f"Dep: {trip['dep_time']}")
            print(f"      Legs: {leg_str}")
            for leg in trip['legs']:
                if leg['trav_time']:
                    print(f"        {leg['mode']}: trav_time={leg['trav_time']}")

# Show sample PT-selected agents
print(f"\n{'#'*70}")
print(f"# A. AGENTS STILL USING PT (selected plan contains PT)")
print(f"{'#'*70}")

count = 0
for pid, data in list(pt_selected.items())[:8]:
    print_agent(pid, data, "PT-SELECTED")
    count += 1

# Show sample PT-rejected agents (PT was tried but walk/car was better)
print(f"\n{'#'*70}")
print(f"# B. AGENTS WHO REJECTED PT (PT in alt plan, walk/car selected)")
print(f"{'#'*70}")

count = 0
for pid, data in list(pt_unselected.items())[:8]:
    print_agent(pid, data, "PT-REJECTED")
    count += 1

# ============================================================
# Score comparison: PT plans vs non-PT plans
# ============================================================
print(f"\n{'#'*70}")
print(f"# C. SCORE COMPARISON: PT vs non-PT plans")
print(f"{'#'*70}")

pt_scores = []
nonpt_scores = []
score_diffs = []  # (person, pt_score, nonpt_score, diff)

for pid, data in agents_data.items():
    pt_plan_scores = []
    nonpt_plan_scores = []
    
    for plan in data['plans']:
        score = plan.get('score')
        if score is None or math.isnan(score):
            continue
        
        modes = set(t['main_mode'] for t in plan.get('trips', []))
        if 'pt' in modes:
            pt_plan_scores.append(score)
            pt_scores.append(score)
        else:
            nonpt_plan_scores.append(score)
            nonpt_scores.append(score)
    
    if pt_plan_scores and nonpt_plan_scores:
        best_pt = max(pt_plan_scores)
        best_nonpt = max(nonpt_plan_scores)
        score_diffs.append({
            'person': pid,
            'best_pt_score': round(best_pt, 2),
            'best_nonpt_score': round(best_nonpt, 2),
            'diff': round(best_nonpt - best_pt, 2),
            'pt_wins': best_pt > best_nonpt
        })

print(f"\nAgents with both PT and non-PT plans: {len(score_diffs)}")

if score_diffs:
    pt_wins = sum(1 for d in score_diffs if d['pt_wins'])
    nonpt_wins = len(score_diffs) - pt_wins
    print(f"  PT wins (higher score): {pt_wins} ({pt_wins/len(score_diffs)*100:.1f}%)")
    print(f"  Non-PT wins: {nonpt_wins} ({nonpt_wins/len(score_diffs)*100:.1f}%)")
    
    diffs = [d['diff'] for d in score_diffs]
    import statistics
    print(f"\n  Score difference (nonPT - PT):")
    print(f"    Mean: {statistics.mean(diffs):.2f}")
    print(f"    Median: {statistics.median(diffs):.2f}")
    print(f"    Min: {min(diffs):.2f} (PT much better)")
    print(f"    Max: {max(diffs):.2f} (Walk/Car much better)")
    
    # Show some examples where PT loses badly
    score_diffs.sort(key=lambda x: x['diff'], reverse=True)
    print(f"\n  Top 10 cases where non-PT beats PT most:")
    for d in score_diffs[:10]:
        print(f"    {d['person']}: PT={d['best_pt_score']}, "
              f"nonPT={d['best_nonpt_score']}, diff={d['diff']}")
    
    print(f"\n  Top 10 cases where PT beats non-PT:")
    for d in score_diffs[-10:]:
        print(f"    {d['person']}: PT={d['best_pt_score']}, "
              f"nonPT={d['best_nonpt_score']}, diff={d['diff']}")

# Overall score stats
if pt_scores and nonpt_scores:
    print(f"\n  Overall score distributions:")
    print(f"    PT plans:     mean={statistics.mean(pt_scores):.2f}, "
          f"median={statistics.median(pt_scores):.2f}, n={len(pt_scores)}")
    print(f"    Non-PT plans: mean={statistics.mean(nonpt_scores):.2f}, "
          f"median={statistics.median(nonpt_scores):.2f}, n={len(nonpt_scores)}")

# Save results
results = {
    'pt_selected_count': len(pt_selected),
    'pt_rejected_count': len(pt_unselected),
    'score_comparison': {
        'agents_with_both': len(score_diffs),
        'pt_wins': pt_wins if score_diffs else 0,
        'nonpt_wins': nonpt_wins if score_diffs else 0,
        'mean_diff': round(statistics.mean(diffs), 2) if score_diffs else 0,
        'median_diff': round(statistics.median(diffs), 2) if score_diffs else 0,
    }
}
with open(f"{OUTPUT_DIR}/visualizations/pt_score_analysis.json", 'w') as f:
    json.dump(results, f, indent=2)

print(f"\nSaved: {OUTPUT_DIR}/visualizations/pt_score_analysis.json")
