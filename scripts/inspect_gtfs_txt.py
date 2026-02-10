import os

BASE_DIR = "2024-TM-PT-GTFS 대중교통GTFS(2023년 기준)/202303_GTFS_DataSet"
FILES = ["agency.txt", "calendar.txt", "routes.txt", "stops.txt", "trips.txt", "stop_times.txt"]

with open("gtfs_txt_inspection.txt", "w", encoding="utf-8") as out:
    for file in FILES:
        path = os.path.join(BASE_DIR, file)
        print(f"=== Inspecting {file} ===", file=out)
        try:
            with open(path, 'r', encoding='utf-8-sig') as f: # standard GTFS is usually utf-8 without BOM, but sometimes with BOM
                header = f.readline().strip()
                print(f"Header: {header}", file=out)
                print("First 3 rows:", file=out)
                for _ in range(3):
                    line = f.readline().strip()
                    if line:
                        print(line, file=out)
        except Exception as e:
            print(f"Error: {e}", file=out)
        print("\n", file=out)
