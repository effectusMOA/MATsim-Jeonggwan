import pandas as pd
import os

BASE_DIR = "2024-TM-PT-GTFS 대중교통GTFS(2023년 기준)"
FILES = [
    "202303_GTFS_route세부정보.xlsx",
    "202303_GTFS_도시철도환승정보.xlsx"
]

with open("gtfs_excel_inspection.txt", "w", encoding="utf-8") as f:
    for file in FILES:
        path = os.path.join(BASE_DIR, file)
        print(f"=== Inspecting {file} ===", file=f)
        try:
            xl = pd.ExcelFile(path)
            print(f"Sheet Names: {xl.sheet_names}", file=f)
            for sheet in xl.sheet_names:
                print(f"\n--- Sheet: {sheet} ---", file=f)
                df = pd.read_excel(path, sheet_name=sheet, nrows=5)
                print(f"Columns: {list(df.columns)}", file=f)
                print(df.head(3).to_string(), file=f)
        except Exception as e:
            print(f"Error: {e}", file=f)
        print("\n", file=f)
