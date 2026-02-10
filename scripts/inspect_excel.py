import pandas as pd

excel_file = r"C:\Users\user\Documents\matsim-berlin\정관읍_합성인구_2023_ver1_260207.xlsx"

try:
    df = pd.read_excel(excel_file, nrows=5)
    print("Columns:")
    print(df.columns.tolist())
    print("\nFirst 5 rows:")
    print(df.head())
    print("\nData Types:")
    print(df.dtypes)
except Exception as e:
    print(f"Error reading Excel file: {e}")
