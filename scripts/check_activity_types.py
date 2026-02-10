import pandas as pd

excel_file = r"C:\Users\user\Documents\matsim-berlin\정관읍_합성인구_2023_ver1_260207.xlsx"

try:
    df = pd.read_excel(excel_file)
    unique_types = set()
    for i in range(1, 8):
        col = f'위치{i}'
        if col in df.columns:
            unique_types.update(df[col].dropna().unique())
            
    print("Unique Activity Types:", unique_types)
except Exception as e:
    print(f"Error: {e}")
