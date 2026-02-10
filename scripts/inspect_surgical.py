import pandas as pd
import sys

# Set display options to avoid truncation
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', 1000)

DEF_FILE = "0. 2016년 가구통행실태조사_데이터정의서.xlsx"
DATA_FILE = "정관읍.xlsx"

with open("inspection_results.txt", "w", encoding="utf-8") as f:
    print("=== DEFINITION FILE INSPECTION ===", file=f)
    try:
        xl_def = pd.ExcelFile(DEF_FILE)
        print(f"Sheet Names: {xl_def.sheet_names}", file=f)
        
        # Target specific sheets for codes
        # Added '직업' to find job codes
        for sheet in xl_def.sheet_names:
            if any(x in sheet for x in ["수단", "목적", "통행", "코드", "행정동", "직업"]):
                print(f"\n--- Sheet: {sheet} ---", file=f)
                df = pd.read_excel(DEF_FILE, sheet_name=sheet)
                print(df.head(30).to_string(), file=f)
                
    except Exception as e:
        print(f"Error reading definition file: {e}", file=f)

    print("\n=== DATA FILE INSPECTION ===", file=f)
    try:
        xl_data = pd.ExcelFile(DATA_FILE)
        print(f"Sheet Names: {xl_data.sheet_names}", file=f)
        
        for sheet in xl_data.sheet_names:
            print(f"\n--- Sheet: {sheet} ---", file=f)
            df = pd.read_excel(DATA_FILE, sheet_name=sheet, nrows=5)
            print(f"Columns: {list(df.columns)}", file=f)
            print("First 2 rows:", file=f)
            print(df.head(2).to_string(), file=f)
            
    except Exception as e:
        print(f"Error reading data file: {e}", file=f)
