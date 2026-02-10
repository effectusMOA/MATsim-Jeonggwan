import pandas as pd

FILE_PATH = "0. 2016년 가구통행실태조사_데이터정의서.xlsx"

print(f"Inspecting {FILE_PATH}...")

try:
    xl = pd.ExcelFile(FILE_PATH)
    print(f"Sheet names: {xl.sheet_names}")
    
    # Target specific sheets for codes
    target_sheets = [s for s in xl.sheet_names if any(x in s for x in ['수단', '목적', '통행', '코드'])]
    
    for sheet in target_sheets:
        print(f"\n--- Sheet: {sheet} ---")
        df = pd.read_excel(FILE_PATH, sheet_name=sheet, nrows=20)
        print(df.to_string()) # Use to_string to avoid truncation

        
except Exception as e:
    print(f"Error: {e}")
