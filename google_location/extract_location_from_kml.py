import xml.etree.ElementTree as ET
from geopy.geocoders import Nominatim
import requests

# Initialize the geocoder
geolocator = Nominatim(user_agent="your_app_name")  # Replace "your_app_name" with a custom name for your app

# Parse the KML file
kml_file = "location_data_2021-09-01.kml"
tree = ET.parse(kml_file)
root = tree.getroot()

# Extract the coordinates from the KML file
coordinates = root.findall(".//{http://www.opengis.net/kml/2.2}coord")

# Get city and country information for each coordinate
for coord in coordinates:
    lat, lon, _ = coord.text.split(',')
    location = geolocator.reverse(f"{lat}, {lon}")

    city = location.raw["address"].get("town") or location.raw["address"].get("city")
    country = location.raw["address"].get("country")

    print(f"Latitude: {lat}, Longitude: {lon}, City: {city}, Country: {country}")
