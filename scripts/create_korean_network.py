import osmium
import geopandas as gpd
from shapely.geometry import Point, LineString
import pandas as pd
import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

# 설정
OSM_FILE = "south-korea-latest.osm.pbf"
STD_LINK_PATH = "NODE_LINK/MOCT_LINK.shp"
OUTPUT_FILE = "input/jeonggwan-network.xml"
# 정관읍 BBox (추정치: 129.12, 35.28, 129.25, 35.38)
BBOX = {'left': 129.12, 'bottom': 35.28, 'right': 129.25, 'top': 35.38} 

print("1. OSM 데이터 로딩 및 필터링 (Jeonggwan)...")

class OSMHandler(osmium.SimpleHandler):
    def __init__(self, bbox):
        super().__init__()
        self.nodes = {}
        self.ways = []
        self.bbox = bbox
        
    def node(self, n):
        # BBox 필터링
        if (self.bbox['left'] <= n.location.lon <= self.bbox['right'] and 
            self.bbox['bottom'] <= n.location.lat <= self.bbox['top']):
            self.nodes[n.id] = (n.location.lon, n.location.lat)
    
    def way(self, w):
        if 'highway' in w.tags:
            # 노드가 모두 로드되었는지 확인 (BBox 내)
            valid_nodes = [n.ref for n in w.nodes if n.ref in self.nodes]
            if len(valid_nodes) > 1:
                self.ways.append({
                    'way_id': w.id,
                    'highway': w.tags.get('highway'),
                    'name': w.tags.get('name', ''),
                    'maxspeed': w.tags.get('maxspeed', ''),
                    'lanes': w.tags.get('lanes', ''),
                    'nodes': valid_nodes
                })

handler = OSMHandler(BBOX)
handler.apply_file(OSM_FILE)
print(f"   - 로드된 링크 수: {len(handler.ways)}")

print("2. GeoDataFrame 생성 및 좌표계 변환...")
ways_gdf = gpd.GeoDataFrame(handler.ways)
ways_gdf['geometry'] = ways_gdf['nodes'].apply(
    lambda nodes: LineString([handler.nodes[n] for n in nodes])
)
ways_gdf.set_crs(epsg=4326, inplace=True)
ways_gdf = ways_gdf.to_crs(epsg=5179) # 한국 좌표계로 변환

print("3. 표준노드링크 로딩...")
if os.path.exists(STD_LINK_PATH):
    std_links = gpd.read_file(STD_LINK_PATH, encoding='euc-kr') # 인코딩 주의
    std_links = std_links.to_crs(epsg=5179)
    print(f"   - 표준노드링크 수: {len(std_links)}")
    
    print("4. 공간 조인 (속성 결합)...")
    # 필요한 컬럼만 선택
    # 실제 컬럼명 확인 필요 (보통 MAX_SPD, LANES, ROAD_RANK 등)
    # 여기서는 일반적인 이름을 가정하고, 없으면 try-except로 처리하거나 확인
    cols_to_use = ['geometry']
    for col in ['MAX_SPD', 'LANES', 'ROAD_RANK']:
        if col in std_links.columns:
            cols_to_use.append(col)
            
    osm_with_std = gpd.sjoin_nearest(
        ways_gdf, 
        std_links[cols_to_use], 
        how='left',
        max_distance=20 # 20m 이내 매칭
    )
else:
    print("   ! 표준노드링크 파일을 찾을 수 없습니다. OSM 속성만 사용합니다.")
    osm_with_std = ways_gdf
    osm_with_std['MAX_SPD'] = None
    osm_with_std['LANES'] = None
    osm_with_std['ROAD_RANK'] = None

# 기본값 설정 함수
def get_default_speed(highway_type, matched_speed):
    if pd.notna(matched_speed) and matched_speed > 0:
        return float(matched_speed)
    
    defaults = {
        'motorway': 100, 'trunk': 80, 'primary': 60, 
        'secondary': 50, 'tertiary': 40, 'residential': 30
    }
    return defaults.get(highway_type, 30)

def get_default_lanes(highway_type, matched_lanes):
    if pd.notna(matched_lanes) and matched_lanes > 0:
        return int(matched_lanes)
        
    defaults = {
        'motorway': 4, 'trunk': 4, 'primary': 2, 
        'secondary': 2, 'tertiary': 1, 'residential': 1
    }
    return defaults.get(highway_type, 1)

# 용량 매핑 (veh/h/lane)
CAPACITY_PER_LANE = {
    1: 2000, 2: 1800, 3: 1600, 4: 1400, 5: 1200, 6: 800
}

print("5. MATSim Network XML 생성...")
root = ET.Element('network')
root.set('xmlns', 'http://www.matsim.org/files/dtd')

nodes_elem = ET.SubElement(root, 'nodes')
links_elem = ET.SubElement(root, 'links')

node_map = {} # (x, y) -> node_id
node_counter = 1

# 링크 처리
for idx, row in osm_with_std.iterrows():
    coords = list(row.geometry.coords)
    
    # 노드 처리 및 ID 할당
    path_node_ids = []
    for x, y in coords:
        if (x, y) not in node_map:
            node_id = str(node_counter)
            node_map[(x, y)] = node_id
            
            node = ET.SubElement(nodes_elem, 'node')
            node.set('id', node_id)
            node.set('x', str(x))
            node.set('y', str(y))
            node_counter += 1
        path_node_ids.append(node_map[(x, y)])
    
    # 링크 생성 (OSM 웨이는 여러 세그먼트로 나뉠 수 있음)
    # 여기서는 단순화를 위해 웨이 전체를 하나의 링크로 하지 않고, 
    # 세그먼트별로 나누는 것이 MATSim의 정석이지만, 
    # OSM 노드들이 교차점일 수 있으므로 세그먼트 단위 생성이 맞음.
    
    speed_kmh = get_default_speed(row['highway'], row.get('MAX_SPD'))
    freespeed = speed_kmh / 3.6
    
    lanes = get_default_lanes(row['highway'], row.get('LANES'))
    
    rank = int(row.get('ROAD_RANK', 4)) if pd.notna(row.get('ROAD_RANK')) else 4
    capacity = lanes * CAPACITY_PER_LANE.get(rank, 1200)
    
    for i in range(len(path_node_ids) - 1):
        from_node = path_node_ids[i]
        to_node = path_node_ids[i+1]
        
        link = ET.SubElement(links_elem, 'link')
        link.set('id', f"{row['way_id']}_{i}")
        link.set('from', from_node)
        link.set('to', to_node)
        
        # 길이 계산
        p1 = Point(coords[i])
        p2 = Point(coords[i+1])
        length = p1.distance(p2)
        link.set('length', f"{length:.2f}")
        
        link.set('freespeed', f"{freespeed:.2f}")
        link.set('capacity', f"{capacity:.1f}")
        link.set('permlanes', f"{lanes}")
        link.set('modes', 'car,bike,walk')
        
        attrs = ET.SubElement(link, 'attributes')
        attr = ET.SubElement(attrs, 'attribute')
        attr.set('name', 'type')
        attr.set('class', 'java.lang.String')
        attr.text = str(row['highway'])

# 저장
print(f"6. 파일 저장: {OUTPUT_FILE}")
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

# 예쁘게 저장
xml_str = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write(xml_str)

print("완료!")
