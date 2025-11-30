# Klein Duimpje: GPX Route Visualizer

A demonstrator project showcasing how to build a fully static, WASM-powered web application using Shinylive to visualize GPX route files from a GitHub repository.

## 🎯 Project Purpose

This repository serves as a practical example of:

1. **Static Shinylive Deployment**: Building interactive data applications that run entirely in the browser without backend servers
2. **Vibecoding with LLMs**: Developed through conversational AI-driven development to rapidly prototype and iterate on design decisions
3. **Modern Python Stack**: Demonstrating WASM-compatible libraries and deployment patterns

## 🚀 Live Demo

Visit the live application: `https://yourusername.github.io/kleinduimpje/`

## 🏗️ Architecture & Design Decisions

### 1. Shinylive for Static Deployment

**Decision**: Use Shinylive instead of traditional Shiny Server

**Rationale**:
- Zero server infrastructure required - the entire app runs in the browser via WASM (Pyodide)
- Free hosting on GitHub Pages
- Instant loading after initial download
- Perfect for demonstration and educational purposes

**Trade-offs**:
- Limited to WASM-compatible Python packages
- Initial load time for downloading Python runtime
- Cannot use system-level libraries (e.g., Fiona, GDAL)

### 2. XML Parsing Instead of Fiona

**Decision**: Use `xml.etree.ElementTree` for GPX parsing instead of Fiona/GDAL

**Rationale**:
- Fiona requires GDAL, which has C dependencies incompatible with WASM
- GPX files are XML-based and can be parsed with pure Python libraries
- `xml.etree.ElementTree` is part of Python's standard library, reducing bundle size

**Implementation**:
```python
def parse_gpx_content(content, filename):
    root = ET.fromstring(content)
    ns = {'gpx': 'http://www.topografix.com/GPX/1/1'}
    
    for trkpt in root.findall('.//gpx:trkpt', ns):
        lat = float(trkpt.get('lat'))
        lon = float(trkpt.get('lon'))
        points.append((lat, lon))
```

### 3. GitHub as Data Source

**Decision**: Fetch GPX files directly from GitHub repository using GitHub API

**Rationale**:
- Eliminates need for backend storage or file upload mechanisms
- Version control for route data
- Easy collaboration and contribution workflow
- Free and reliable hosting

**Implementation**:
```python
async def fetch_gpx_list():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GPX_FOLDER}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url, timeout=10.0)
        # Process files...
```

### 4. Async/Await Pattern

**Decision**: Use async functions for all network operations

**Rationale**:
- Prevents blocking the UI during file fetching
- Enables responsive loading indicators
- Better user experience with multiple GPX files
- Native support in Shiny for Python

### 5. Modular Card Components

**Decision**: Implement map visualizations as Shiny modules

**Rationale**:
- Encapsulation of map logic and state
- Reusability across multiple GPX files
- Clear separation of concerns
- Easier testing and maintenance

**Implementation**:
```python
@module.ui
def gpx_map_ui():
    return ui.div(
        ui.card(
            ui.card_header(ui.output_text("card_title")),
            output_widget("map_widget"),
            height="400px"
        )
    )

@module.server
def gpx_map_server(input, output, session, download_url, file_name):
    # Module logic...
```

### 6. Horizontal Flexbox Layout

**Decision**: Use CSS flexbox for horizontal card arrangement

**Rationale**:
- Responsive design that adapts to screen size
- Natural wrapping behavior for many routes
- Simple implementation without complex grid systems
- Supports horizontal scrolling on narrow screens

**Implementation**:
```python
ui.div(
    *[gpx_map_ui(f["name"]) for f in files],
    style="display: flex; gap: 20px; flex-wrap: wrap; overflow-x: auto;"
)
```

### 7. ipyleaflet for Map Visualization

**Decision**: Use ipyleaflet instead of folium or other mapping libraries

**Rationale**:
- Native Jupyter widget integration with Shiny
- Interactive maps with smooth pan/zoom
- WASM-compatible (pure JavaScript/Python)
- Rich feature set for route visualization

## 📦 Dependencies

All dependencies are WASM-compatible:

- **shiny**: Web application framework
- **shinywidgets**: Bridge for Jupyter widgets in Shiny
- **ipyleaflet**: Interactive maps
- **httpx**: Async HTTP client for API calls
- **shinyswatch**: Bootstrap themes (optional)

## 🛠️ Development Workflow

### Local Development

```bash
# Install dependencies with uv
uv pip install shiny shinywidgets ipyleaflet httpx shinyswatch

# Run locally
shiny run app.py
```

### Configuration

Update these variables in `app.py`:

```python
GITHUB_REPO = "yourusername/yourrepo"
GITHUB_BRANCH = "main"
GPX_FOLDER = "data"
```

### Testing Shinylive Export

```bash
# Install shinylive CLI
uv pip install shinylive

# Export to static site
shinylive export . site

# Test locally
python -m http.server -d site 8080
```

## 🚢 Deployment

The app automatically deploys to GitHub Pages via GitHub Actions on every push to `main`.

**Workflow**: `.github/workflows/deploy-shinylive.yml`

Key features:
- Uses `uv` for fast dependency installation
- Exports app with `shinylive export`
- Deploys to GitHub Pages with artifact upload

## 🧪 Vibecoding Development Process

This project was developed through conversational AI-driven development ("vibecoding"), demonstrating:

1. **Rapid Prototyping**: Quick iteration from initial concept to working demo
2. **Problem-Solving**: Real-time debugging and architectural decisions
3. **Best Practices**: Incorporating modern Python tooling (uv, ruff, polars concepts)
4. **Documentation**: Comprehensive explanation of design rationale

### Key Iterations

1. Started with Fiona-based local file reading
2. Pivoted to XML parsing for WASM compatibility
3. Integrated GitHub API for remote file access
4. Fixed decorator ordering and async patterns
5. Refined UI layout and theming

## 📝 Lessons Learned

### What Works Well

✅ Pure Python approach enables full static deployment  
✅ GitHub as data source is elegant and version-controlled  
✅ Shinylive removes deployment complexity  
✅ Modular design scales well with multiple routes

### Limitations

⚠️ Initial load time for WASM runtime (~10-20s)  
⚠️ Limited to WASM-compatible packages  
⚠️ GitHub API rate limits (60 requests/hour unauthenticated)  
⚠️ Large GPX files may impact browser performance

### Future Enhancements

- Add caching for GitHub API responses
- Implement route statistics (distance, elevation)
- Support additional file formats (KML, GeoJSON)
- Add route comparison features
- Enable authentication for private repos

## 📄 License

MIT License - Feel free to use this as a template for your own projects.

## 🙏 Acknowledgments

Built with:
- [Shiny for Python](https://shiny.posit.co/py/)
- [Shinylive](https://shiny.posit.co/py/docs/shinylive.html)
- [ipyleaflet](https://ipyleaflet.readthedocs.io/)
- Claude (Anthropic) for vibecoding assistance (tried Gemini 3 Pro, too, but that ended up in a loop with errors it could not fix by itself)

---



## Personal notes: playing around with Garmin files on Marimo

### Functional requirements

I want to free my Garmin `.fit` and `.gpx` files, which gives me a good excuse to play around with Marimo:

- Garmin allows me to download all my `.fit` files in bulk; `.gpx` files can be donwloaded one at a time on [Garmin Connect](https://connect.garmin.com)
- Using [OpenTracks](https://opentracksapp.com/) on my Android phone, with which I can collect and build my own library of my favourite tracks and routes
- Workflow:
    - Export `.fit` from Garming
    - Convert to `.gpx` and import in OpenTracks
    - Add pictures etc. and save as [`.kmz`](https://developers.google.com/kml/documentation/kmzarchives)
    - `.kmz` can be re-imported into Garmin

### Technicalities

Trying to keep the project as light as possible, hence no geopandas, polars, pyogrio, fiona, shapely etc.

TO DO:

- Manually download `.fit` files work, but bulk downloaded export are empty