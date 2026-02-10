import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import box

STD_LINK_PATH = "NODE_LINK/MOCT_LINK.shp"
OUTPUT_IMAGE = "input/std_link_visualization.png"

# 정관읍 BBox (Same as before)
BBOX_COORDS = [129.12, 35.28, 129.25, 35.38] # minx, miny, maxx, maxy

print(f"Loading Standard Node Link from {STD_LINK_PATH}...")

try:
    # Read file (this might take a moment for the full file)
    # For efficiency, we can try to read with a bbox filter if supported, 
    # but geopandas read_file with bbox requires the file to be spatially indexed or small enough.
    # Since we don't know if it's indexed, we'll read and clip.
    # Warning: Reading 275MB SHP might be slow.
    
    # Optimization: Read only geometry first or use bbox if possible
    # Geopandas 0.11+ supports bbox in read_file
    bbox_geom = box(*BBOX_COORDS)
    
    # Note: The SHP seems to be in EPSG:5174 (Old Korean Central, Bessel 1841) based on the coordinates.
    # Sample bounds: [174321, 248555, 371713, 516108]
    # We need to convert BBox to EPSG:5174 to filter, then reproject data to 5179 for consistency if needed, 
    # or just plot in 5174. Let's plot in 5174 to be safe and fast.
    
    import pyproj
    from shapely.ops import transform
    
    wgs84 = pyproj.CRS('EPSG:4326')
    # Trying EPSG:5174 (Korean 1985 Modified Central Belt) which is common for older MOCT data
    # Or EPSG:5186 (GRS80 Central Belt)? No, 5186 is similar to 5174 but GRS80.
    # The coordinates 174k, 248k look like 5174 (y is northing, x is easting).
    # Wait, 5179 is x~900k, y~1.7m. 
    # 5174 is x~200k, y~500k? 
    # Let's try to project our WGS84 bbox to 5174 and see if it overlaps.
    
    target_crs = pyproj.CRS('EPSG:5174') 
    project = pyproj.Transformer.from_crs(wgs84, target_crs, always_xy=True).transform
    
    bbox_target = transform(project, bbox_geom)
    minx, miny, maxx, maxy = bbox_target.bounds
    print(f"BBox in EPSG:5174: {minx:.1f}, {miny:.1f}, {maxx:.1f}, {maxy:.1f}")
    
    print("Reading and filtering data (assuming EPSG:5174)...")
    # We read without CRS check first, then set it manually if missing
    gdf = gpd.read_file(STD_LINK_PATH, bbox=bbox_target, encoding='euc-kr')
    
    # If still 0, try 5181, 5186...
    if len(gdf) == 0:
        print("Still 0 links. Trying EPSG:5186...")
        target_crs = pyproj.CRS('EPSG:5186')
        project = pyproj.Transformer.from_crs(wgs84, target_crs, always_xy=True).transform
        bbox_target = transform(project, bbox_geom)
        minx, miny, maxx, maxy = bbox_target.bounds
        print(f"BBox in EPSG:5186: {minx:.1f}, {miny:.1f}, {maxx:.1f}, {maxy:.1f}")
        gdf = gpd.read_file(STD_LINK_PATH, bbox=bbox_target, encoding='euc-kr')
        
    print(f"Loaded {len(gdf)} links in the area.")
    
    if len(gdf) == 0:
        print("No links found in the bounding box. Checking coordinate system...")
        # Fallback: Read first few rows to check CRS/Bounds
        gdf_sample = gpd.read_file(STD_LINK_PATH, rows=5, encoding='euc-kr')
        print("Sample bounds:", gdf_sample.total_bounds)
    else:
        print("Plotting...")
        fig, ax = plt.subplots(figsize=(12, 12))
        
        gdf.plot(ax=ax, color='blue', linewidth=0.5, alpha=0.7)
        
        plt.title(f"Standard Node Link (MOCT) Visualization: Jeonggwan-eup\nLinks: {len(gdf)}")
        plt.xlabel("X Coordinate (EPSG:5179)")
        plt.ylabel("Y Coordinate (EPSG:5179)")
        plt.grid(True, alpha=0.3)
        
        print(f"Saving image to {OUTPUT_IMAGE}...")
        plt.savefig(OUTPUT_IMAGE, dpi=150, bbox_inches='tight')
        print("Done!")

except Exception as e:
    print(f"Error: {e}")
