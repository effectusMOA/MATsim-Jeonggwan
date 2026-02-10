"""
Analyze 정관_test.xlsx data structure and coordinate ranges
"""

import pandas as pd
import xml.etree.ElementTree as ET

print("=" * 60)
print("정관_test.xlsx 분석")
print("=" * 60)

# Load Excel data
df = pd.read_excel('정관_test.xlsx')

print("\n=== 주거지 좌표 범위 ===")
print(f"X: {df['주거지_X좌표'].min():.0f} ~ {df['주거지_X좌표'].max():.0f}")
print(f"Y: {df['주거지_Y좌표'].min():.0f} ~ {df['주거지_Y좌표'].max():.0f}")

print("\n=== 역외통행 데이터 확인 ===")
out_area = df[df['역외통행'] == 1]
print(f'역외통행 수: {len(out_area)}')
if len(out_area) > 0:
    print(out_area[['agent_ucode', '사슬타입', '위치2', '위치2_X좌표', '위치2_Y좌표']].head(5))

print("\n=== 위치2 좌표 범위 (직장/학교) ===")
print(f"X: {df['위치2_X좌표'].min():.0f} ~ {df['위치2_X좌표'].max():.0f}")
print(f"Y: {df['위치2_Y좌표'].min():.0f} ~ {df['위치2_Y좌표'].max():.0f}")

print("\n" + "=" * 60)
print("네트워크 좌표 확인")
print("=" * 60)

# Load network
tree = ET.parse('input/jeonggwan-network.xml')
root = tree.getroot()

nodes = root.findall('.//node')[:10]
print(f"\n네트워크 노드 수: {len(root.findall('.//node'))}")
print("\n=== 샘플 노드 좌표 ===")
for node in nodes[:5]:
    print(f"ID: {node.get('id')}, X: {node.get('x')}, Y: {node.get('y')}")

# Get coordinate range from network
all_x = [float(n.get('x')) for n in root.findall('.//node')]
all_y = [float(n.get('y')) for n in root.findall('.//node')]
print(f"\n=== 네트워크 좌표 범위 ===")
print(f"X: {min(all_x):.0f} ~ {max(all_x):.0f}")
print(f"Y: {min(all_y):.0f} ~ {max(all_y):.0f}")

print("\n=== 좌표계 비교 ===")
print(f"Excel 주거지 X 범위: {df['주거지_X좌표'].min():.0f} ~ {df['주거지_X좌표'].max():.0f}")
print(f"Network X 범위:     {min(all_x):.0f} ~ {max(all_x):.0f}")
print(f"\nExcel 주거지 Y 범위: {df['주거지_Y좌표'].min():.0f} ~ {df['주거지_Y좌표'].max():.0f}")
print(f"Network Y 범위:     {min(all_y):.0f} ~ {max(all_y):.0f}")
