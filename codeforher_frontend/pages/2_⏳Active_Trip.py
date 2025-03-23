import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
from streamlit_extras.switch_page_button import switch_page
import time
import polyline
from datetime import datetime, timezone
import os
from dotenv import load_dotenv

# Base URL of your FastAPI backend
BASE_URL = "http://localhost:8080/api"

# Page config
st.set_page_config(
    page_title="Active Trip - Women Commute Safety",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 10px;
        background-color: #FF4B4B;
        color: white;
        border: none;
        padding: 10px 20px;
        border-radius: 5px;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
    }
    .map-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .trip-details-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .emergency-section {
        background-color: #FFF5F5;
        border-radius: 10px;
        padding: 20px;
        border: 1px solid #FFE5E5;
        margin-bottom: 1rem;
    }
    .sos-button {
        background-color: #DC3545 !important;
        color: white !important;
        font-weight: bold !important;
        padding: 15px !important;
        font-size: 1.1em !important;
    }
    .sos-button:hover {
        background-color: #C82333 !important;
    }
    .contact-card {
        background-color: white;
        border-radius: 8px;
        padding: 15px;
        margin-bottom: 10px;
        border: 1px solid #eee;
    }
    .trip-header {
        color: #333;
        font-size: 1.2em;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .status-badge {
        background-color: #28A745;
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.9em;
        font-weight: 500;
        display: inline-block;
        margin-left: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# Check if user is logged in and has an active trip
if "token" not in st.session_state:
    st.warning("Please login to access the active trip page.")
    switch_page("Login")
    st.stop()

if not st.session_state.get("is_trip_started", False):
    st.warning("No active trip found. Please start a trip first.")
    switch_page("Trip_Planner")
    st.stop()

# Function to fetch user details including emergency contacts
def fetch_user_details():
    try:
        response = requests.get(
            f"{BASE_URL}/users/get-users",
            headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error fetching user details: {e}")
        return None

# Function to send emergency message
def send_emergency_message(contact_id, message):
    try:
        response = requests.post(
            f"{BASE_URL}/emergency/send-message",
            json={
                "user_id": st.session_state.token["user_id"],
                "contact_id": contact_id,
                "message": message
            },
            headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
        )
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error sending message: {e}")
        return False

# Add the get_current_location function
def get_current_location() -> dict:
    """
    Get current location based on IP address.

    Useful for when you need to determine the user's current location.
    This tool retrieves geolocation data based on the IP address.

    Returns:
        dict: A dictionary containing location information including address,
              latitude, longitude, city, country, etc.
    """
    load_dotenv()
    try:
        # Make request to IP geolocation API
        response = requests.get("https://ipinfo.io/json")
        if response.status_code != 200:
            raise ValueError(f"Failed to get location data: {response.status_code}")

        ip_data = response.json()

        # Extract location coordinates from the response (format: "latitude,longitude")
        if "loc" in ip_data:
            lat, lon = ip_data["loc"].split(",")

            # Format response
            location_data = {
                "ip": ip_data.get("ip", ""),
                "city": ip_data.get("city", ""),
                "region": ip_data.get("region", ""),
                "country": ip_data.get("country", ""),
                "postal": ip_data.get("postal", ""),
                "latitude": lat,
                "longitude": lon,
                "address": f"{ip_data.get('city', '')}, {ip_data.get('region', '')}, {ip_data.get('country', '')}",
            }
            return location_data
        else:
            raise ValueError("Location coordinates not found in the response")

    except Exception as e:
        raise ValueError(f"Error getting current location: {str(e)}")

# Update the broadcast_sos function
def broadcast_sos(message):
    try:
        # Get current location using IP geolocation
        try:
            location_data = get_current_location()
            current_location = {
                "latitude": float(location_data["latitude"]),
                "longitude": float(location_data["longitude"]),
                "address": location_data["address"]
            }
        except Exception as loc_error:
            st.error(f"Error getting current location: {loc_error}")
            # Fallback to trip details or route data
            current_location = None
            location_address = ""
            if "trip_details" in st.session_state and "current_location" in st.session_state.trip_details:
                current_location = {
                    "latitude": st.session_state.trip_details["current_location"]["latitude"],
                    "longitude": st.session_state.trip_details["current_location"]["longitude"],
                    "address": st.session_state.trip_details.get("current_address", "")
                }
            elif "route_data" in st.session_state and "routes" in st.session_state.route_data:
                route = st.session_state.route_data["routes"][0]
                current_location = {
                    "latitude": route["legs"][0]["start_location"]["lat"],
                    "longitude": route["legs"][0]["start_location"]["lng"],
                    "address": route["legs"][0].get("start_address", "")
                }

        if not current_location:
            st.error("Could not determine current location")
            return False

        # Prepare SOS message payload
        sos_payload = {
            "user_id": st.session_state.token["user_id"],
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "location": current_location,
            "message": message
        }
        
        # Send SOS alert
        response = requests.post(
            f"{BASE_URL}/sos/send-alert",
            json=sos_payload,
            headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
        )
        
        return response.status_code == 200
    except Exception as e:
        st.error(f"Error broadcasting SOS: {e}")
        return False

# Header with Trip Status
st.title("⏳ Active Trip")
st.markdown('<span class="status-badge">IN PROGRESS</span>', unsafe_allow_html=True)

# Main content
col1, col2 = st.columns([2, 1])

with col1:
    # Map Section
    st.markdown('<div class="trip-header">📍 Live Location</div>', unsafe_allow_html=True)
    st.markdown('<div class="map-container">', unsafe_allow_html=True)
    if "route_map" in st.session_state:
        folium_static(st.session_state.route_map, width=None, height=400)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Trip Details
    st.markdown('<div class="trip-details-card">', unsafe_allow_html=True)
    st.markdown('<div class="trip-header">🚗 Trip Details</div>', unsafe_allow_html=True)
    
    # Trip metrics
    if "trip_details" in st.session_state:
        details = st.session_state.trip_details
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Distance", f"{details['distance']/1000:.1f} km")
        with metric_col2:
            st.metric("Duration", f"{details['duration']/60:.0f} mins")
        with metric_col3:
            st.metric("ETA", time.strftime("%I:%M %p", time.localtime(time.time() + details['duration'])))
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    # Emergency Section
    st.markdown('<div class="emergency-section">', unsafe_allow_html=True)
    st.markdown('<div class="trip-header">🚨 Emergency Options</div>', unsafe_allow_html=True)
    
    # SOS Message Input
    sos_message = st.text_area(
        "SOS Message",
        placeholder="Enter your emergency message here...",
        help="This message will be sent to all your emergency contacts",
        key="sos_message"
    )
    
    # SOS Button
    if st.button("🚨 BROADCAST SOS ALERT", key="sos", type="primary", help="Alert all emergency contacts"):
        if not sos_message:
            sos_message = "Help! I am in danger."  # Default message if none provided
        if broadcast_sos(sos_message):
            st.success("SOS alert sent to all emergency contacts!")
        else:
            st.error("Failed to send SOS alert. Please try again.")
        
        # Fetch user details for emergency contacts
        user_details = fetch_user_details()
        if user_details and "emergency_contacts" in user_details:
            contacts = user_details["emergency_contacts"]
            selected_contact = st.selectbox(
                "Select Contact",
                options=[f"{contact['name']} ({contact['phone']})" for contact in contacts],
                format_func=lambda x: x
            )
        
        message = st.text_area("Message", placeholder="Enter your message here...")
        
        if st.button("Send Message", key="send_msg"):
            # Get contact_id from selected contact
            contact_idx = contacts[st.session_state.contact_index]["id"]
            if send_emergency_message(contact_idx, message):
                st.success("Message sent successfully!")
            else:
                st.error("Failed to send message. Please try again.")
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Trip Control Buttons
    st.markdown('<div class="trip-details-card">', unsafe_allow_html=True)
    st.markdown('<div class="trip-header">🎯 Trip Controls</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Complete Trip", key="complete", type="primary"):
            try:
                response = requests.get(
                    f"{BASE_URL}/commute/end-trip/{st.session_state.trip_id}",
                    headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
                )
                if response.status_code == 200:
                    st.session_state.is_trip_started = False
                    st.session_state.trip_id = None
                    st.success("Trip completed successfully!")
                    time.sleep(2)
                    switch_page("Trip_Planner")
            except Exception as e:
                st.error(f"Error completing trip: {e}")
    
    with col2:
        if st.button("Cancel Trip", key="cancel"):
            try:
                response = requests.get(
                    f"{BASE_URL}/commute/cancel-trip/{st.session_state.trip_id}",
                    headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
                )
                if response.status_code == 200:
                    st.session_state.is_trip_started = False
                    st.session_state.trip_id = None
                    st.success("Trip cancelled successfully!")
                    time.sleep(2)
                    switch_page("Trip_Planner")
            except Exception as e:
                st.error(f"Error cancelling trip: {e}")
    
    st.markdown('</div>', unsafe_allow_html=True)

# Auto-refresh the page every 30 seconds to update location
st.markdown(
    """
    <script>
        setTimeout(function(){
            window.location.reload();
        }, 30000);
    </script>
    """,
    unsafe_allow_html=True
) 