from pathlib import Path
import gpxpy
from shiny import App, ui, module, reactive, render
from shinywidgets import output_widget, render_widget
from ipyleaflet import Map, Polyline, basemaps

# --- Helper: Parse GPX with gpxpy (Robust) ---
def get_gpx_data(file_path):
    points = []
    name = Path(file_path).stem 
    
    try:
        # Open the file uploaded by Shiny
        with open(file_path, 'r', encoding='utf-8') as gpx_file:
            gpx = gpxpy.parse(gpx_file)
        
        # 1. Try to get the internal track name
        if gpx.tracks and gpx.tracks[0].name:
            name = gpx.tracks[0].name
        elif gpx.routes and gpx.routes[0].name:
            name = gpx.routes[0].name

        # 2. Extract points (lat, lon) only
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    points.append((point.latitude, point.longitude))
                    
        # 3. If no tracks, check for routes
        if not points:
            for route in gpx.routes:
                for point in route.points:
                    points.append((point.latitude, point.longitude))

    except Exception as e:
        print(f"Error parsing {file_path}: {e}")
        return f"Error: {name}", (52.0, 5.0), []

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
def gpx_map_ui(id, display_name):
    """
    Defines the UI for a single map card.
    Args:
        id: The unique namespace ID (required by @module.ui).
        display_name: The text to show in the card header.
    """
    return ui.card(
        ui.card_header(display_name),
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

app_ui = ui.page_fluid(
    ui.h2("Klein Duimpje: Route Visualizer"),
    ui.p("Select multiple .gpx files to visualize them vertically."),
    
    ui.input_file(
        "gpx_upload", 
        "Choose GPX Files", 
        multiple=True, 
        accept=[".gpx"]
    ),
    
    ui.hr(),
    ui.output_ui("gpx_cards"),
    class_="p-3"
)

def server(input, output, session):
    
    # Store the processed files info: list of (name, path, unique_id)
    processed_files = reactive.Value([])

    @reactive.Effect
    @reactive.event(input.gpx_upload)
    def _():
        files = input.gpx_upload()
        if not files:
            return
            
        current_list = []
        for f in files:
            f_name = f['name']
            f_path = f['datapath']
            # Create a simple safe ID from the filename
            safe_id = "".join(x for x in f_name if x.isalnum())
            
            # Store tuple: (Display Name, File Path, ID)
            current_list.append((f_name, f_path, safe_id))
            
            # Spin up the module server using the ID
            gpx_map_server(safe_id, f_path)
            
        processed_files.set(current_list)

    @render.ui
    def gpx_cards():
        files = processed_files.get()
        if not files:
            return ui.div(ui.p("No files loaded.", class_="text-muted"))
        
        # --- CRITICAL FIX IS HERE ---
        # We pass TWO arguments to gpx_map_ui:
        # 1. f[2] -> The ID
        # 2. f[0] -> The Display Name
        return ui.div(*[gpx_map_ui(f[2], f[0]) for f in files])

app = App(app_ui, server)