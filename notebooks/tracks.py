import marimo

__generated_with = "0.18.0"
app = marimo.App(width="medium")


@app.cell
def _():
    import marimo as mo
    return (mo,)


@app.cell
def _(mo):
    from fit2gpx import convert_fit_to_gpx
    import gpxpy
    import folium
    from folium.plugins import MousePosition


    f = mo.ui.file(kind="area", filetypes=[".gpx", ".fit"], multiple=False)
    mo.vstack([mo.md("Please upload a .gpx or .fit file with a course that you want to view"), f])
    return MousePosition, convert_fit_to_gpx, f, folium, gpxpy


@app.cell
def _(MousePosition, convert_fit_to_gpx, f, folium, gpxpy):
    map_start_zoom = 13
    try:
        match f.name().split(".")[-1]:
            case "gpx":
                gpx = gpxpy.parse(f.contents())
            case "fit":
                gpx = gpxpy.parse(convert_fit_to_gpx(f.contents()))
    except Exception as e:
        m = folium.Map()
    else:
        track_coordinates = []
        for track in gpx.tracks:
            for segment in track.segments:
                for point in segment.points:
                    track_coordinates.append((point.latitude, point.longitude))

        # Initialize the map centered on the starting point of the track
        start_coords = track_coordinates[0]
        m = folium.Map(location=start_coords, zoom_start=map_start_zoom, tiles="Cartodb Positron")

        # A. Draw the Track Line
        folium.PolyLine(locations=track_coordinates, color="red", weight=4, opacity=0.8, tooltip="GPX Track").add_to(m)

        # B. Add Start and End Markers (Green and Red)
        # Start
        folium.Marker(location=track_coordinates[0], popup="Start", icon=folium.Icon(color="green", icon="play")).add_to(m)

        # End
        folium.Marker(location=track_coordinates[-1], popup="End", icon=folium.Icon(color="red", icon="stop")).add_to(m)

        # C. Automatically fit the map bounds to the track
        m.fit_bounds(m.get_bounds())
        MousePosition().add_to(m)
    return gpx, m


@app.cell
def _(m):
    m
    return


@app.cell
def _(gpx):
    gpx
    return


@app.cell
def _():
    return


if __name__ == "__main__":
    app.run()
