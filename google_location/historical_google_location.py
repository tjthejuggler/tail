import requests
from datetime import date

# Replace these with your own session cookies
cookies = {
    "SID": "your_SID_cookie",
    "HSID": "your_HSID_cookie",
    "SSID": "your_SSID_cookie"
}

# Specify the date you want to get location data for
target_date = date(2023, 3, 29)

# Construct the request URL
url = f"https://www.google.com/maps/timeline/kml?authuser=0&pb=!1m8!1m3!1i{target_date.year}!2i{target_date.month - 1}!3i{target_date.day}"

# Send the request with the cookies
response = requests.get(url, cookies=cookies)

# Check if the request was successful
if response.status_code == 200:
    # Save the KML data to a file
    with open(f"location_data_{target_date}.kml", "wb") as f:
        f.write(response.content)
else:
    print("Failed to fetch location data:", response.status_code, response.reason)
