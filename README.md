# Playing around with Garmin files on Marimo

## Functional requirements

I want to free my Garmin `.fit` and `.gpx` files, which gives me a good excuse to play around with Marimo:

- Garmin allows me to download all my `.fit` files in bulk; `.gpx` files can be donwloaded one at a time on [Garmin Connect](https://connect.garmin.com)
- Using [OpenTracks](https://opentracksapp.com/) on my Android phone, with which I can collect and build my own library of my favourite tracks and routes
- Workflow:
    - Export `.fit` from Garming
    - Convert to `.gpx` and import in OpenTracks
    - Add pictures etc. and save as [`.kmz`](https://developers.google.com/kml/documentation/kmzarchives)
    - `.kmz` can be re-imported into Garmin

## Technicalities

Trying to keep the project as light as possible, hence no geopandas, polars, pyogrio, fiona, shapely etc.

TO DO:

- Manually download `.fit` files work, but bulk downloaded export are empty