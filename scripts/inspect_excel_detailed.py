import pandas as pd

excel_file = r"C:\Users\user\Documents\matsim-berlin\정관읍_합성인구_2023_ver1_260207.xlsx"

try:
    df = pd.read_excel(excel_file, nrows=1)
    print("All Columns:")
    for col in df.columns:
        print(col)
    
    print("\nFirst Row Data:")
    row = df.iloc[0].to_dict()
    for k, v in row.items():
        print(f"{k}: {v}")

except Exception as e:
    print(f"Error: {e}")
