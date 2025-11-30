from pathlib import Path
import fiona

GPX_DIR = Path("./data") 
gpx_files = list(GPX_DIR.glob("*.gpx"))

if not gpx_files:
    print("No .gpx files found to test.")

for file_path in gpx_files:
    print(f"\n--- Checking {file_path.name} ---")
    try:
        layers = fiona.listlayers(file_path)
        print(f"Layers found: {layers}")
        
        target_layer = 'tracks' if 'tracks' in layers else 'routes' if 'routes' in layers else None
        
        if target_layer:
            with fiona.open(file_path, layer=target_layer) as src:
                print(f"Opened layer: {target_layer}, Feature count: {len(src)}")
                if len(src) > 0:
                    first_feat = next(iter(src))
                    geom_type = first_feat['geometry']['type']
                    coords = first_feat['geometry']['coordinates']
                    print(f"Geometry Type: {geom_type}")
                    
                    # Check first coordinate to see if it is 2D or 3D
                    sample_coord = None
                    if geom_type == 'LineString':
                        sample_coord = coords[0]
                    elif geom_type == 'MultiLineString':
                        sample_coord = coords[0][0]
                        
                    print(f"Sample Coordinate: {sample_coord} (Length: {len(sample_coord)})")
        else:
            print("No suitable track/route layer found.")
            
    except Exception as e:
        print(f"ERROR: {e}")