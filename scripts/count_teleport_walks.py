import gzip
import xml.etree.ElementTree as ET
import glob

# Configuration
BASE_DIR = "output/jeonggwan-v6-regional-multimode"

# Find latest plans file
def get_latest_plans_file(base_dir):
    plans_files = glob.glob(f"{base_dir}/ITERS/it.*/???.plans.xml.gz") + glob.glob(f"{base_dir}/ITERS/it.*/*.plans.xml.gz")
    if not plans_files:
        if glob.glob(f"{base_dir}/*.output_plans.xml.gz"):
            return glob.glob(f"{base_dir}/*.output_plans.xml.gz")[0]
        return None
    
    def extract_iter(f):
        try:
            return int(f.split('it.')[1].split('\\')[0].split('/')[0])
        except:
            return -1
    plans_files.sort(key=extract_iter)
    return plans_files[-1]

PLANS_FILE = get_latest_plans_file(BASE_DIR)
print(f"Counting Teleport Walks in: {PLANS_FILE}")

def get_distance(x1, y1, x2, y2):
    return ((x1 - x2)**2 + (y1 - y2)**2)**0.5

count_total = 0
count_walk = 0
count_d10 = 0
count_d20 = 0
count_d50 = 0

try:
    with gzip.open(PLANS_FILE, 'rt', encoding='utf-8') as f:
        print("Scannng plans...")
        context = ET.iterparse(f, events=('end',))
        
        for event, elem in context:
            if elem.tag == 'plan' and elem.get('selected') == 'yes':
                legs = elem.findall('leg')
                activities = elem.findall('activity')
                
                for i, leg in enumerate(legs):
                    count_total += 1
                    
                    if leg.get('mode') == 'walk':
                        count_walk += 1
                        
                        if i < len(activities) - 1:
                            act_from = activities[i]
                            act_to = activities[i+1]
                            try:
                                x1, y1 = float(act_from.get('x')), float(act_from.get('y'))
                                x2, y2 = float(act_to.get('x')), float(act_to.get('y'))
                                dist = get_distance(x1, y1, x2, y2)
                                
                                if dist > 10000: count_d10 += 1
                                if dist > 20000: count_d20 += 1
                                if dist > 50000: count_d50 += 1
                                
                            except:
                                pass
            
            if elem.tag == 'person':
                elem.clear() # Clear memory
        
    print(f"\nTrip Statistics:")
    print(f"Total Trips: {count_total}")
    print(f"Total Walk Trips: {count_walk} ({100*count_walk/count_total:.1f}%)")
    print("-" * 30)
    print(f"Walk > 10km: {count_d10} ({100*count_d10/count_total:.1f}%)")
    print(f"Walk > 20km: {count_d20} ({100*count_d20/count_total:.1f}%)")
    print(f"Walk > 50km: {count_d50} ({100*count_d50/count_total:.1f}%)")
    print("\nConclusion: These trips are candidates for exclusion.")

except Exception as e:
    print(f"Error: {e}")
