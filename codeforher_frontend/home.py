import streamlit as st
import requests
import pandas as pd
from io import BytesIO
from PIL import Image

# Ola Maps API credentials (replace with your own)
CLIENT_ID = "d2ab2b3d-acbe-42dc-a29e-3302e9211bce"
API_KEY = "z97QFxxgDKsgcmJBQGFTwII7TQKOAMlOmkqiZICy"
STATIC_TILES_URL = "https://api.olamaps.io/tiles/v1/styles/{styleName}/static/{lon},{lat},{zoom}/{width}x{height}.{format}"


# Function to fetch static map image from Ola Maps Static Tiles API
def get_static_map(lat, lon, zoom=15, width=800, height=600, style_name="default-light-standard", format="png"):
    url = STATIC_TILES_URL.format(
        styleName=style_name,
        lon=lon,
        lat=lat,
        zoom=zoom,
        width=width,
        height=height,
        format=format
    )
    params = {
        "api_key": API_KEY
    }
    headers = {
        "X-Request-Id": "Streamlit-Map-Request",  # Replace with a unique ID if needed
        "X-Client-Id": CLIENT_ID
    }

    response = requests.get(url, headers=headers, params=params)

    if response.status_code == 200:
        return Image.open(BytesIO(response.content))
    else:
        st.error(f"API request failed: {response.status_code} - {response.text}")
        return None


# Streamlit app
st.title("Ola Maps Static Tiles with Streamlit")

# User input for coordinates and options
lat = st.number_input(
    "Latitude", value=12.93, format="%.6f", help="Latitude of the map center (e.g., 12.93 for Bengaluru)"
    )
lon = st.number_input(
    "Longitude", value=77.61, format="%.6f", help="Longitude of the map center (e.g., 77.61 for Bengaluru)"
    )
zoom = st.slider("Zoom Level", min_value=1, max_value=20, value=15, help="Zoom level of the map")
width = st.slider("Image Width", min_value=200, max_value=1200, value=800, step=50)
height = st.slider("Image Height", min_value=200, max_value=1200, value=600, step=50)
style_name = st.selectbox("Map Style", ["default-light-standard", "default-dark-standard"], index=0)

if st.button("Generate Map"):
    if lat and lon:
        # Fetch the static map image
        map_image = get_static_map(lat, lon, zoom, width, height, style_name)

        if map_image:
            st.success(f"Map generated for Latitude {lat}, Longitude {lon}")
            # Display the image in Streamlit
            st.image(map_image, caption=f"Map at ({lat}, {lon}) with zoom {zoom}", use_container_width=True)

            # Optionally display coordinates on a simple map for reference
            map_data = pd.DataFrame({"lat": [lat], "lon": [lon]})
            st.map(map_data, zoom=zoom)
    else:
        st.warning("Please provide valid latitude and longitude values.")

# Run the app with: streamlit run your_script.py