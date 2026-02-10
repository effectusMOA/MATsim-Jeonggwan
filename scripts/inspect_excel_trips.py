import pandas as pd

excel_file = r"C:\Users\user\Documents\matsim-berlin\정관읍_합성인구_2023_ver1_260207.xlsx"

try:
    # Read a chunk to find an agent with trips
    df = pd.read_excel(excel_file, nrows=1000)
    
    # Filter for agents with trips (사슬길이 > 0)
    agents_with_trips = df[df['사슬길이'] > 0]
    
    if not agents_with_trips.empty:
        row = agents_with_trips.iloc[0].to_dict()
        print("Agent with trips found:")
        for k, v in row.items():
            if pd.notna(v):
                print(f"{k}: {v}")
    else:
        print("No agents with trips found in the first 1000 rows.")

except Exception as e:
    print(f"Error: {e}")
