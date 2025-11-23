import fitparse
import gpxpy
import gpxpy.gpx
from datetime import datetime
import os
import sys

# XML namespace for Garmin TrackPoint Extensions (v1)
# This allows us to store HR, Cadence, and Temp in the GPX file
NSMAP = {"gpxtpx": "http://www.garmin.com/xmlschemas/TrackPointExtension/v1"}


def convert_fit_to_gpx(input_source, output_dest=None):
    """
    Converts a Garmin .fit file to a .gpx file.

    Args:
        input_source: A file path (str) or a file-like object containing .fit data.
        output_dest: A file path (str), a file-like object to write to, or None.
                     If None and input is a file path, writes to a .gpx file with same name.
                     If None and input is a file object, returns the GPX XML string.
    """

    is_file_path = isinstance(input_source, str)

    if is_file_path:
        if not os.path.exists(input_source):
            print(f"Error: File {input_source} not found.")
            return
        print(f"Parsing: {input_source}...")
    else:
        print("Parsing provided file-like object...")

    # Load the FIT file
    try:
        # fitparse accepts both file paths and file-like objects
        fitfile = fitparse.FitFile(input_source)
    except fitparse.utils.FitParseError as e:
        print(f"Error parsing .fit file: {e}")
        return

    # Initialize GPX object
    gpx = gpxpy.gpx.GPX()

    # Create a track and segment
    gpx_track = gpxpy.gpx.GPXTrack()
    gpx.tracks.append(gpx_track)
    gpx_segment = gpxpy.gpx.GPXTrackSegment()
    gpx_track.segments.append(gpx_segment)

    # Register the namespace for extensions (HR/Cadence)
    gpx.nsmap.update(NSMAP)

    points_added = 0

    # Iterate over all messages of type 'record' (actual track points)
    for record in fitfile.get_messages("record"):
        # Extract data from the record
        record_data = record.get_values()

        lat = record_data.get("position_lat")
        lon = record_data.get("position_long")
        ele = record_data.get("altitude")
        timestamp = record_data.get("timestamp")

        # Valid track points must have lat, lon, and time
        if lat is not None and lon is not None and timestamp is not None:
            # FIT files use semicircles for Lat/Lon sometimes.
            # fitparse usually converts this based on units, but valid degrees are -90 to 90.
            # If the value is huge (int), it needs conversion: degrees = semicircles * (180 / 2^31)
            if abs(lat) > 90 or abs(lon) > 180:
                lat = lat * (180.0 / 2**31)
                lon = lon * (180.0 / 2**31)

            # Create the GPX Point
            gpx_point = gpxpy.gpx.GPXTrackPoint(
                latitude=lat, longitude=lon, elevation=ele, time=timestamp
            )

            # --- Handle Extensions (HR, Cadence, Temp) ---
            # We use ElementTree to build the XML structure for Garmin extensions
            from xml.etree import ElementTree as ET

            hr = record_data.get("heart_rate")
            cad = record_data.get("cadence")
            temp = record_data.get("temperature")

            if hr is not None or cad is not None or temp is not None:
                # Create the extension structure
                extensions = ET.Element("extensions")
                tpx = ET.SubElement(extensions, "gpxtpx:TrackPointExtension")

                if hr is not None:
                    et_hr = ET.SubElement(tpx, "gpxtpx:hr")
                    et_hr.text = str(hr)

                if cad is not None:
                    et_cad = ET.SubElement(tpx, "gpxtpx:cad")
                    et_cad.text = str(cad)

                if temp is not None:
                    et_temp = ET.SubElement(tpx, "gpxtpx:atemp")
                    et_temp.text = str(temp)

                gpx_point.extensions.append(extensions)

            # Add point to segment
            gpx_segment.points.append(gpx_point)
            points_added += 1

    # Generate XML string
    xml_data = gpx.to_xml()

    # Determine Output behavior
    if output_dest is None:
        if is_file_path:
            base_name = os.path.splitext(input_source)[0]
            output_dest = f"{base_name}.gpx"
        else:
            # Return string if input was an object and no output specified
            return xml_data

    # Write to file path
    if isinstance(output_dest, str):
        print(f"Writing {points_added} points to {output_dest}...")
        try:
            with open(output_dest, "w") as f:
                f.write(xml_data)
            print("Conversion successful!")
        except Exception as e:
            print(f"Error writing GPX file: {e}")
    # Write to file-like object
    elif hasattr(output_dest, "write"):
        try:
            output_dest.write(xml_data)
            print(f"Written {points_added} points to output stream.")
        except Exception as e:
            print(f"Error writing to output stream: {e}")


if __name__ == "__main__":
    # Simple CLI usage
    if len(sys.argv) < 2:
        print("Usage: python fit_to_gpx.py <input_file.fit> [output_file.gpx]")
    else:
        input_fit = sys.argv[1]
        output_gpx = sys.argv[2] if len(sys.argv) > 2 else None

        convert_fit_to_gpx(input_fit, output_gpx)
