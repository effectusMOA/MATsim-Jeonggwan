"""
Convert DRT boardings CSV to GeoPackage for SimWrapper visualization
"""
import pandas as pd

# Read the boardings CSV
base_path = 'output/jeonggwan-multimode'
df = pd.read_csv(f'{base_path}/null-multimode.output_drt_boardings_drt.csv', sep=';')

print('Original columns:', df.columns.tolist())
print(f'Total records: {len(df)}')

# Calculate total boardings per stop (sum of all hourly columns)
hourly_cols = [col for col in df.columns if ':' in col]
df['total_boardings'] = df[hourly_cols].sum(axis=1)

# Keep only essential columns
df_simple = df[['Link', 'x', 'y', 'total_boardings']].copy()
df_simple = df_simple[df_simple['total_boardings'] > 0]  # Only stops with activity

print(f'Stops with boardings: {len(df_simple)}')
print(df_simple.head(10))

# Try to create GeoPackage (requires geopandas)
try:
    import geopandas as gpd
    from shapely.geometry import Point
    
    # Create geometry
    geometry = [Point(xy) for xy in zip(df_simple['x'], df_simple['y'])]
    gdf = gpd.GeoDataFrame(df_simple, geometry=geometry, crs="EPSG:5186")  # Korean coordinate system
    
    # Convert to WGS84 for web maps
    gdf = gdf.to_crs("EPSG:4326")
    
    # Save as GeoPackage  
    output_gpkg = f'{base_path}/drt_boardings_stops.gpkg'
    gdf.to_file(output_gpkg, driver='GPKG')
    print(f'\nGeoPackage saved: {output_gpkg}')
    print('SimWrapper will now auto-detect this file!')
    
except ImportError:
    print('\ngeopandas not installed. Saving as CSV with proper naming...')
    output_csv = f'{base_path}/drt_boardings_points.csv'
    df_simple.to_csv(output_csv, sep=';', index=False)
    print(f'CSV saved: {output_csv}')
