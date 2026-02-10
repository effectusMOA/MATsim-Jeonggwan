import pandas as pd
import numpy as np

excel_file = "정관읍_합성인구_2023_ver1_260207.xlsx"
print(f"Loading {excel_file}...")

# Read full file
df = pd.read_excel(excel_file)
total_agents = len(df)

print(f"Total Agents: {total_agents}")

# Check value distributions
print("\n--- Value Distribution ---")
print("운전면허 (License):")
print(df['운전면허'].value_counts(dropna=False))

print("\n가구주 (Household Head):")
print(df['가구주'].value_counts(dropna=False))

# Current Logic: License only
# Assuming 1 = Yes, 0 = No based on typical data, but checking value counts will confirm
# If strict '유/무', we adapt.
license_col = '운전면허'
head_col = '가구주'

# Normalize values (adapt based on output if needed, but for now assuming 1/0 or similar)
# Let's clean up
df['has_license'] = df[license_col].apply(lambda x: 1 if str(x) in ['1', '1.0', '유', 'Yes'] else 0)
df['is_head'] = df[head_col].apply(lambda x: 1 if str(x) in ['1', '1.0', '유', 'Yes'] else 0)

current_owners = df[df['has_license'] == 1]
new_owners = df[(df['has_license'] == 1) & (df['is_head'] == 1)]

print("\n--- Car Ownership Analysis ---")
print(f"Current Logic (License Only):")
print(f"  Count: {len(current_owners):,}")
print(f"  Ratio: {len(current_owners)/total_agents*100:.1f}%")

print(f"\nNew Logic (License + Household Head):")
print(f"  Count: {len(new_owners):,}")
print(f"  Ratio: {len(new_owners)/total_agents*100:.1f}%")


# Detailed Breakdown
print("\n" + "="*50)
print("상세 분석 (가구주 x 운전면허)")
print("="*50)


# Crosstab
crosstab = pd.crosstab(df['is_head'], df['has_license'], margins=True, margins_name="Total")

# Rename index/columns safely
idx_map = {0: "비가구주 (Non-Head)", 1: "가구주 (Head)", "Total": "Total"}
col_map = {0: "면허 없음 (No Lic)", 1: "면허 있음 (Lic)", "Total": "Total"}

crosstab = crosstab.rename(index=idx_map, columns=col_map)

print("\n1. 인원 수 (Counts):")
print(crosstab)

# Percentages based on Total Population
norm_total = pd.crosstab(df['is_head'], df['has_license'], margins=True, margins_name="Total", normalize='all') * 100
norm_total = norm_total.rename(index=idx_map, columns=col_map)

print("\n2. 전체 대비 비율 (%):")
print(norm_total.round(1))

# Percentages within Household Head Group
norm_index = pd.crosstab(df['is_head'], df['has_license'], margins=True, margins_name="Total", normalize='index') * 100
norm_index = norm_index.rename(index=idx_map, columns=col_map)

print("\n3. 그룹 내 비율 (Row %):")
print("(예: 가구주 중에서 면허 있는 사람 비율)")
print(norm_index.round(1))
