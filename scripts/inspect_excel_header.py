import pandas as pd

excel_file = "정관읍_합성인구_2023_ver1_260207.xlsx"
print(f"Loading {excel_file}...")

# Read first few rows to inspect columns
df = pd.read_excel(excel_file, nrows=10)

print("\nColumns:")
for i, col in enumerate(df.columns):
    print(f"{i}: {col}")

print("\nFirst 5 rows (relevant cols):")
# Try to find relevant columns
potential_cols = [c for c in df.columns if any(x in str(c).lower() for x in ['lic', 'rel', 'head', 'household', 'car', 'id'])]
print(df[potential_cols].head())
