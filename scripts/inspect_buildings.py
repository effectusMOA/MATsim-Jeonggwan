import geopandas as gpd
import os

BASE_DIR = "건물"
SUBDIRS = [
    "GIMI9_GEOCODE_20251229_152402_층별개요_정관읍_주거용건물",
    "GIMI9_GEOCODE_20251229_171304_층별개요_정관읍_비주거용건물",
    "GIMI9_GEOCODE_20251229_171949_층별개요_정관읍_비주거_공장",
    "GIMI9_GEOCODE_20251229_175933_층별개요_정관읍_비주거_비공장"
]

# Map subdir to a short name
NAMES = {
    "GIMI9_GEOCODE_20251229_152402_층별개요_정관읍_주거용건물": "Residential",
    "GIMI9_GEOCODE_20251229_171304_층별개요_정관읍_비주거용건물": "Non-Residential (All)",
    "GIMI9_GEOCODE_20251229_171949_층별개요_정관읍_비주거_공장": "Factory",
    "GIMI9_GEOCODE_20251229_175933_층별개요_정관읍_비주거_비공장": "Non-Factory"
}

with open("building_inspection.txt", "w", encoding="utf-8") as f:
    print("Inspecting Building Shapefiles...", file=f)

    for subdir in SUBDIRS:
        path = os.path.join(BASE_DIR, subdir)
        # Find .shp file
        shp_file = None
        for file in os.listdir(path):
            if file.endswith(".shp"):
                shp_file = os.path.join(path, file)
                break
                
        if shp_file:
            print(f"\n=== {NAMES[subdir]} ===", file=f)
            print(f"File: {shp_file}", file=f)
            try:
                gdf = gpd.read_file(shp_file, encoding='euc-kr') # Assuming Korean encoding
                print(f"CRS: {gdf.crs}", file=f)
                print(f"Count: {len(gdf)}", file=f)
                print(f"Columns: {list(gdf.columns)}", file=f)
                print("First 3 rows:", file=f)
                # Print specific columns if they look like type info
                cols_to_show = [c for c in gdf.columns if 'geometry' not in c][:10] # Show first 10 non-geom cols
                print(gdf[cols_to_show].head(3).to_string(), file=f)
            except Exception as e:
                print(f"Error: {e}", file=f)
        else:
            print(f"No .shp found in {subdir}", file=f)

