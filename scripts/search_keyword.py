import pandas as pd

DEF_FILE = "0. 2016년 가구통행실태조사_데이터정의서.xlsx"
KEYWORD = "직업"

print(f"Searching for '{KEYWORD}' in {DEF_FILE}...")

try:
    xl = pd.ExcelFile(DEF_FILE)
    for sheet in xl.sheet_names:
        df = pd.read_excel(DEF_FILE, sheet_name=sheet)
        # Check if keyword exists in any string column
        mask = df.apply(lambda x: x.astype(str).str.contains(KEYWORD, na=False))
        if mask.any().any():
            print(f"\n--- Found in Sheet: {sheet} ---")
            # Print rows where keyword is found
            rows = df[mask.any(axis=1)]
            print(rows.to_string())
            
except Exception as e:
    print(f"Error: {e}")
