from pathlib import Path
import fiona
from shiny import App, ui, module
from shinywidgets import output_widget, render_widget
from ipyleaflet import Map, Polyline, basemaps

# --- Configuration ---
GPX_DIR = Path("./data") 

# --- Helper: Parse GPX with Fiona (Robust) ---
def get_gpx_data(file_path):
    points = []
    name = file_path.name # Default to filename
    
    try:
        # Check available layers
        layers = fiona.listlayers(file_path)
        target_layer = 'tracks' if 'tracks' in layers else 'routes' if 'routes' in layers else None

        if target_layer:
            with fiona.open(file_path, layer=target_layer) as src:
                # FIX: Do not call len(src). Iterate directly.
                for i, feature in enumerate(src):
                    
                    # Attempt to grab the route name from the first feature
                    if i == 0:
                        props = feature.get('properties', {})
                        if 'name' in props and props['name']:
                            name = props['name']

                    # Extract Geometry
                    geom = feature['geometry']
                    raw_coords = []
                    
                    if geom['type'] == 'MultiLineString':
                        for line in geom['coordinates']:
                            raw_coords.extend(line)
                    elif geom['type'] == 'LineString':
                        raw_coords = geom['coordinates']
                    
                    # Process coordinates
                    for p in raw_coords:
                        # Ensure we have at least 2 coords (lon, lat)
                        if len(p) >= 2:
                            # Fiona gives (Lon, Lat, [Ele]), Ipyleaflet needs (Lat, Lon)
                            points.append((p[1], p[0]))

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")

    # Calculate center
    if points:
        avg_lat = sum(p[0] for p in points) / len(points)
        avg_lon = sum(p[1] for p in points) / len(points)
        center = (avg_lat, avg_lon)
    else:
        center = (52.0, 5.0)

    return name, center, points

# --- Shiny Module: Map Card ---
@module.ui
def gpx_map_ui(name):
    return ui.card(
        ui.card_header(name),
        output_widget("map_widget"),
        style="margin-bottom: 20px; height: 400px;"
    )

@module.server
def gpx_map_server(input, output, session, file_path):
    @render_widget
    def map_widget():
        name, center, points = get_gpx_data(file_path)
        
        m = Map(
            basemap=basemaps.OpenStreetMap.Mapnik,
            center=center,
            zoom=13,
            scroll_wheel_zoom=True
        )
        
        if points:
            line = Polyline(
                locations=points,
                color="blue",
                fill=False,
                weight=3
            )
            m.add_layer(line)
            
        return m

# --- Main Application ---
gpx_files = sorted(list(GPX_DIR.glob("*.gpx")))

app_ui = ui.page_fluid(
    ui.h2("Klein Duimpje: Route Visualizer"),
    ui.p(f"Visualizing {len(gpx_files)} GPX files"),
    *[gpx_map_ui(f.stem, f.name) for f in gpx_files],
    class_="p-3"
)

def server(input, output, session):
    for f in gpx_files:
        gpx_map_server(f.stem, f)

app = App(app_ui, server)