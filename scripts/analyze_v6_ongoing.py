import gzip
import xml.etree.ElementTree as ET
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

import os
import glob

# Configuration
BASE_DIR = "output/jeonggwan-v6-regional-multimode"
MODESTATS_FILE = f"{BASE_DIR}/null-multimode.modestats.csv"

# Find latest plans file
plans_files = glob.glob(f"{BASE_DIR}/ITERS/it.*/???.plans.xml.gz") + glob.glob(f"{BASE_DIR}/ITERS/it.*/*.plans.xml.gz")
if not plans_files:
    print("   No iteration plans files found in ITERS.")
    # Check root
    if os.path.exists(f"{BASE_DIR}/null-multimode.output_plans.xml.gz"):
        PLANS_FILE = f"{BASE_DIR}/null-multimode.output_plans.xml.gz"
        print(f"   Using root plans file: {PLANS_FILE}")
    else:
        PLANS_FILE = None
        print("   WARNING: No plans file found. Skipping detailed analysis.")
else:
    # Sort by iteration number
    # Assumes format .../it.X/X.plans.xml.gz or similar
    def extract_iter(f):
        try:
            return int(f.split('it.')[1].split('\\')[0].split('/')[0])
        except:
            return -1
            
    plans_files.sort(key=extract_iter)
    PLANS_FILE = plans_files[-1]
    ITERATION = extract_iter(PLANS_FILE)
    print(f"   Found latest plans file: {PLANS_FILE} (Iteration {ITERATION})")

print(f"Analyzing v6 Simulation...")

# 1. Mode Share Trend
print("1. Reading Mode Stats Trend...")
try:
    modestats = pd.read_csv(MODESTATS_FILE, sep='\t')
    latest_share = modestats.iloc[-1]
    print(f"   Latest Iteration: {latest_share['Iteration']}")
    print("   Current Shares:")
    for col in modestats.columns:
        if col != 'Iteration':
            print(f"     {col}: {latest_share[col]:.2f}%")
            
    # Plot Trend
    plt.figure(figsize=(10, 6))
    for col in modestats.columns:
        if col != 'Iteration':
            plt.plot(modestats['Iteration'], modestats[col] * 100, label=col)
    plt.title(f"Mode Share Trend (v6) - Up to It.{latest_share['Iteration']}")
    plt.xlabel("Iteration")
    plt.ylabel("Share (%)")
    plt.legend()
    plt.grid(True)
    plt.savefig(f"{BASE_DIR}/v6_modestats_trend.png")
    print(f"   Saved trend plot to {BASE_DIR}/v6_modestats_trend.png")
except Exception as e:
    print(f"   Failed to read modestats: {e}")

# 2. Detailed Plan Analysis (Age & Distance)
print("\n2. Parsing Executed Plans for Detailed Analysis...")
# We need to parse plans to get: (Person ID -> Subpopulation, Selected Plan -> Routes/Modes)
# Since parsing XML is slow, we'll do a single pass to collect data.

def get_distance(x1, y1, x2, y2):
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

trips_data = []

try:
    with gzip.open(PLANS_FILE, 'rt', encoding='utf-8') as f:
        context = ET.iterparse(f, events=('end',))
        
        current_person_id = None
        subpop = "default"
        
        for event, elem in context:
            if elem.tag == 'person':
                current_person_id = elem.get('id')
                # Reset attributes for new person
                subpop = "default" 
                # Parse attributes if available directly under person or in attributes
                # Standard MATSim: <person><attributes><attribute name="subpopulation">...
                # But iterparse sees 'end' of person after attributes.
                # We need to capture attributes when we see 'attribute' tag or analyze sub-elements.
                # Let's rely on finding selected plan.
                
                # Actually, capturing subpop from sub-elements in iterparse is tricky if we don't track state.
                # Let's find 'plan' with selected='yes'
                selected_plan = elem.find("./plan[@selected='yes']")
                if selected_plan is None:
                    # Maybe only one plan and not marked? usually marked.
                    # Or 'yes' is lowercase.
                    pass
                
                # Let's assume standard structure:
                # We can refine parsing logic:
                # Store person attributes when parsing <person> children.
                pass

            if elem.tag == 'attribute' and elem.get('name') == 'subpopulation':
                 subpop = elem.text

            if elem.tag == 'plan' and elem.get('selected') == 'yes':
                # Process legs
                legs = elem.findall('leg')
                activities = elem.findall('activity') # to get coordinates
                
                # We need pairs of Act -> Leg -> Act to calculate beeline distance
                # Activities corresponding to leg: leg[i] is between act[i] and act[i+1]
                
                for i, leg in enumerate(legs):
                    mode = leg.get('mode')
                    
                    # Routing mode usually in 'trav_time' or main mode
                    # If routing info is lost in plan (sometimes only links), we default to mode.
                    # But usually mode is correct.
                    
                    if i < len(activities) - 1:
                        act_from = activities[i]
                        act_to = activities[i+1]
                        
                        try:
                            x1, y1 = float(act_from.get('x')), float(act_from.get('y'))
                            x2, y2 = float(act_to.get('x')), float(act_to.get('y'))
                            dist = get_distance(x1, y1, x2, y2)
                            
                            trips_data.append({
                                'subpop': subpop,
                                'mode': mode,
                                'distance': dist
                            })
                        except:
                            pass # Missing coords
            
            if elem.tag == 'person':
                elem.clear() # Clear memory
                
    print(f"   Parsed {len(trips_data)} trips.")
    
    df = pd.DataFrame(trips_data)
    
    # Analysis 1: Mode Split by Age
    print("\n   [Age Group Analysis]")
    age_split = pd.crosstab(df['subpop'], df['mode'], normalize='index') * 100
    print(age_split.round(1))
    
    # Analysis 2: Mode Split by Distance
    bins = [0, 1000, 3000, 5000, 10000, 50000, float('inf')]
    labels = ['<1km', '1-3km', '3-5km', '5-10km', '10-50km', '>50km']
    df['dist_bin'] = pd.cut(df['distance'], bins=bins, labels=labels)
    
    print("\n   [Distance Analysis - Mode Share %]")
    dist_split = pd.crosstab(df['dist_bin'], df['mode'], normalize='index') * 100
    print(dist_split.round(1))
    
    # Save results
    with open(f"{BASE_DIR}/v6_analysis_summary.txt", 'w') as f:
        f.write("v6 Simulation Analysis Summary (Iteration 39)\n============================================\n\n")
        f.write("1. Age Group Mode Split (%)\n")
        f.write(age_split.round(1).to_string())
        f.write("\n\n2. Distance Bin Mode Split (%)\n")
        f.write(dist_split.round(1).to_string())

except Exception as e:
    print(f"   Failed to parse plans: {e}")

print("\nAnalysis Complete.")
