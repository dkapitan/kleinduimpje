from io import StringIO
from pathlib import Path
import tomllib

import fsspec
from ipyleaflet import Map, Polyline, basemaps
from shiny import App, ui, reactive, module, render
import shinyswatch
from shinywidgets import output_widget, render_widget
import xml.etree.ElementTree as ET


# --- Configuration from pyproject.toml ---
def load_config():
    """Load GitHub repository configuration from pyproject.toml"""
    pyproject_path = Path("pyproject.toml")

    if pyproject_path.exists():
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

            # Extract repository URL from project metadata
            repo_url = data.get("project", {}).get("urls", {}).get("Repository", "")

            if repo_url:
                # Parse GitHub repo from URL (e.g., https://github.com/user/repo)
                parts = repo_url.rstrip("/").split("/")
                if len(parts) >= 2:
                    return f"{parts[-2]}/{parts[-1]}"

            # Fallback to tool.kleinduimpje section if exists
            tool_config = data.get("tool", {}).get("kleinduimpje", {})
            if "github_repo" in tool_config:
                return tool_config["github_repo"]

    # Default fallback
    return "dkapitan/kleinduimpje"


GITHUB_REPO = load_config()
GITHUB_BRANCH = "main"
GPX_FOLDER = "data"  # Folder in repo containing GPX files


# --- Helper: Fetch GPX files list from GitHub ---
def fetch_gpx_list():
    """Fetch list of GPX files from GitHub repository using fsspec"""
    try:
        # Split repo into org and repo name
        org, repo = GITHUB_REPO.split("/")

        # Initialize GitHub filesystem with org and repo
        fs = fsspec.filesystem("github", org=org, repo=repo, sha=GITHUB_BRANCH)

        # List files in the directory
        files = fs.ls(GPX_FOLDER)

        gpx_files = [{"name": Path(f).name, "path": f} for f in files if f.lower().endswith(".gpx")]
        return gpx_files
    except Exception as e:
        print(f"Error fetching GPX list: {e}")
        return []


# --- Helper: Parse GPX from GitHub ---
def fetch_and_parse_gpx(github_path):
    """Fetch and parse GPX file from GitHub using fsspec"""
    try:
        # Split repo into org and repo name
        org, repo = GITHUB_REPO.split("/")

        # Initialize GitHub filesystem with org and repo
        fs = fsspec.filesystem("github", org=org, repo=repo, sha=GITHUB_BRANCH)

        # Read file content
        with fs.open(github_path, "r") as f:
            content = f.read()

        return parse_gpx_content(content, Path(github_path).name)
    except Exception as e:
        print(f"Error fetching GPX from {github_path}: {e}")
        return None, (52.0, 5.0), []


def parse_gpx_content(content, filename):
    """Parse GPX XML content"""
    points = []
    name = filename.replace(".gpx", "")

    try:
        root = ET.fromstring(content)

        # Define namespace
        ns = {"gpx": "http://www.topografix.com/GPX/1/1"}

        # Try to get track name
        trk_name = root.find(".//gpx:trk/gpx:name", ns)
        if trk_name is not None and trk_name.text:
            name = trk_name.text

        # Extract track points
        for trkpt in root.findall(".//gpx:trkpt", ns):
            lat = float(trkpt.get("lat"))
            lon = float(trkpt.get("lon"))
            points.append((lat, lon))

        # If no track points, try route points
        if not points:
            for rtept in root.findall(".//gpx:rtept", ns):
                lat = float(rtept.get("lat"))
                lon = float(rtept.get("lon"))
                points.append((lat, lon))

    except Exception as e:
        print(f"Error parsing GPX content: {e}")

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
def gpx_map_ui():
    return ui.div(
        ui.card(
            ui.card_header(ui.output_text("card_title")),
            output_widget("map_widget"),
            height="400px",
        ),
        style="min-width: 350px; flex: 1;",
    )


@module.server
def gpx_map_server(input, output, session, github_path, file_name):
    gpx_data = reactive.Value(None)

    @reactive.effect
    def _():
        data = fetch_and_parse_gpx(github_path)
        gpx_data.set(data)

    @render_widget
    def map_widget():
        data = gpx_data.get()

        if data is None:
            # Return empty map while loading
            return Map(basemap=basemaps.OpenStreetMap.Mapnik, center=(52.0, 5.0), zoom=7)

        name, center, points = data

        m = Map(
            basemap=basemaps.OpenStreetMap.Mapnik, center=center, zoom=13, scroll_wheel_zoom=True
        )

        if points:
            line = Polyline(locations=points, color="#2563eb", fill=False, weight=4, opacity=0.8)
            m.add_layer(line)

        return m

    @render.text
    def card_title():
        data = gpx_data.get()
        if data is None:
            return f"Loading {file_name}..."
        return data[0]


# --- Main Application ---
app_ui = ui.page_fillable(
    ui.panel_title("Klein Duimpje: Route Visualizer"),
    ui.div(ui.output_ui("loading_message"), ui.output_ui("maps_container"), class_="p-3"),
    theme=shinyswatch.theme.flatly,
)


def server(input, output, session):
    gpx_files = reactive.Value([])

    @reactive.effect
    def _():
        files = fetch_gpx_list()
        gpx_files.set(files)

    @render.ui
    def loading_message():
        files = gpx_files.get()
        if not files:
            return ui.div(ui.p("Loading GPX files from GitHub...", class_="text-muted"))
        return ui.p(f"Visualizing {len(files)} GPX routes", class_="lead")

    @render.ui
    def maps_container():
        files = gpx_files.get()

        if not files:
            return ui.div()

        # Create horizontally stacked cards
        return ui.div(
            *[gpx_map_ui(f["name"].replace(".gpx", "")) for f in files],
            style="display: flex; gap: 20px; flex-wrap: wrap; overflow-x: auto;",
        )

    # Initialize map servers for each file
    @reactive.effect
    def _():
        files = gpx_files.get()
        for f in files:
            module_id = f["name"].replace(".gpx", "")
            gpx_map_server(module_id, f["path"], f["name"])


app = App(app_ui, server)
