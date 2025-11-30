from pathlib import Path
import gpxpy
from shiny import App, ui, module
from shinywidgets import output_widget, render_widget
from ipyleaflet import Map, Polyline, TileLayer, basemaps

# --- Configuration ---
GPX_DIR = Path("./data")  # Change to "./data" if needed

# --- Helper: Parse GPX ---
def get_gpx_data(file_path):
    """Parses a GPX file and returns name, center_lat, center_lon, and points."""
    with open(file_path, 'r') as gpx_file:
        gpx = gpxpy.parse(gpx_file)
        
    points = []
    name = file_path.name
    
    # Extract points
    for track in gpx.tracks:
        if track.name: name = track.name
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude))
                
    if not points:
        for route in gpx.routes:
            if route.name: name = route.name
            for point in route.points:
                points.append((point.latitude, point.longitude))

    # Calculate center
    if points:
        avg_lat = sum(p[0] for p in points) / len(points)
        avg_lon = sum(p[1] for p in points) / len(points)
        center = (avg_lat, avg_lon)
    else:
        center = (52.0, 5.0) # Default fallback (Netherlands approx)

    return name, center, points

# --- Shiny Module: Map Card ---
# This module handles the UI and Logic for a single GPX card

@module.ui
def gpx_map_ui(name):
    return ui.card(
        ui.card_header(name),
        output_widget("map_widget"), # The ipyleaflet container
        style="margin-bottom: 20px; height: 400px;"
    )

@module.server
def gpx_map_server(input, output, session, file_path):
    @render_widget
    def map_widget():
        name, center, points = get_gpx_data(file_path)
        
        # Create the map centered on the route
        m = Map(
            basemap=basemaps.OpenStreetMap.Mapnik,
            center=center,
            zoom=13,
            scroll_wheel_zoom=True
        )
        
        # Add the route line
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

# Scan for files once at startup to generate the UI structure
gpx_files = sorted(list(GPX_DIR.glob("*.gpx")))

app_ui = ui.page_fluid(
    ui.h2("Klein Duimpje: Route Visualizer (ipyleaflet)"),
    ui.p(f"Visualizing {len(gpx_files)} GPX files from: {GPX_DIR.resolve()}"),
    
    # Generate the UI for every file found
    *[gpx_map_ui(f.stem, f.name) for f in gpx_files],
    
    class_="p-3"
)

def server(input, output, session):
    # Register the server logic for every file found
    for f in gpx_files:
        gpx_map_server(f.stem, f)

app = App(app_ui, server)