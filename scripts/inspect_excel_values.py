import pandas as pd

f = "정관읍_합성인구_2023_ver1_260207.xlsx"
print(f"Reading {f}...")
# Read specific columns to save memory
cols = ['agent_ucode', '연령', '운전면허', '사슬타입', '위치1', '위치2', '위치1_체류시간', '통행1_출발']
df = pd.read_excel(f, usecols=lambda x: x in cols, nrows=10000)

print("=== Unique Values ===")
print(f"License (운전면허): {df['운전면허'].unique()}")
print(f"Loc1 (위치1): {df['위치1'].unique()}")
print(f"Loc2 (위치2): {df['위치2'].unique()}")
print(f"Age (연령) Sample: {df['연령'].head().tolist()}")
print(f"Chain (사슬타입) Sample: {df['사슬타입'].head().tolist()}")
print(f"Duration (체류시간) Sample: {df['위치1_체류시간'].head().tolist()}")
print(f"DepTime (출발) Sample: {df['통행1_출발'].head().tolist()}")
