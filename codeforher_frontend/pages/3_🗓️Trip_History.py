import streamlit as st
import requests
from datetime import datetime
import pytz
from streamlit_extras.switch_page_button import switch_page
import folium
from streamlit_folium import st_folium
import time
import polyline

# Base URL of your FastAPI backend
BASE_URL = "http://localhost:8080/api"

# Page config
st.set_page_config(
    page_title="Trip History",
    page_icon="🗓️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .trip-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .trip-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .trip-date {
        color: #666;
        font-size: 0.9em;
    }
    .status-badge {
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
        font-weight: 500;
        display: inline-block;
    }
    .status-completed {
        background-color: #28A745;
        color: white;
    }
    .status-ongoing {
        background-color: #FFC107;
        color: #000;
    }
    .status-cancelled {
        background-color: #DC3545;
        color: white;
    }
    .trip-details {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1rem;
        margin-bottom: 1rem;
    }
    .detail-item {
        padding: 10px;
        background-color: #f8f9fa;
        border-radius: 5px;
    }
    .detail-label {
        color: #666;
        font-size: 0.85em;
        margin-bottom: 4px;
    }
    .detail-value {
        font-weight: 500;
        color: #333;
    }
    .location-box {
        background-color: #f8f9fa;
        padding: 10px;
        border-radius: 5px;
        margin-bottom: 0.5rem;
    }
    .alert-section {
        margin-top: 1rem;
        padding: 10px;
        background-color: #FFF3CD;
        border-radius: 5px;
    }
    .map-container {
        border-radius: 5px;
        overflow: hidden;
        margin-top: 1rem;
    }
    .filters-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Check if user is logged in
if "token" not in st.session_state:
    st.warning("Please login to view trip history.")
    switch_page("Login")
    st.stop()

# Initialize session state for filters
if "status_filter" not in st.session_state:
    st.session_state.status_filter = "All"
if "sort_by" not in st.session_state:
    st.session_state.sort_by = "Latest First"
if "search_location" not in st.session_state:
    st.session_state.search_location = ""

def fetch_trips():
    """Fetch all trips for the current user."""
    try:
        response = requests.get(
            f"{BASE_URL}/commute/trips",
            params={"user_id": st.session_state.token["user_id"]},
            headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
        )
        if response.status_code == 200:
            return response.json()
        st.error("Failed to fetch trips")
        return []
    except Exception as e:
        st.error(f"Error fetching trips: {e}")
        return []

def create_trip_map(start_location, end_location, route=None):
    """Create a folium map for the trip."""
    center_lat = (start_location["latitude"] + end_location["latitude"]) / 2
    center_lng = (start_location["longitude"] + end_location["longitude"]) / 2
    
    m = folium.Map(location=[center_lat, center_lng], zoom_start=12)
    
    # Add start marker
    folium.Marker(
        [start_location["latitude"], start_location["longitude"]],
        popup="Start",
        icon=folium.Icon(color="green", icon="info-sign"),
    ).add_to(m)
    
    # Add end marker
    folium.Marker(
        [end_location["latitude"], end_location["longitude"]],
        popup="End",
        icon=folium.Icon(color="red", icon="info-sign"),
    ).add_to(m)
    
    # Add route if available
    if route:
        points = [[point["latitude"], point["longitude"]] for point in route]
        folium.PolyLine(points, weight=2, color="blue", opacity=0.8).add_to(m)
    
    return m

def format_datetime(dt_str):
    """Format datetime string to a readable format."""
    dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
    local_tz = pytz.timezone('Asia/Kolkata')
    local_dt = dt.astimezone(local_tz)
    return local_dt.strftime("%d %b %Y, %I:%M %p")

# Page Header
st.title("🗓️ Trip History")

# Filters Section
st.markdown('<div class="filters-card">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    status_filter = st.selectbox(
        "Filter by Status",
        ["All", "Completed", "Ongoing", "Cancelled"],
        key="trip_history_status_filter"
    )
    st.session_state.status_filter = status_filter
with col2:
    sort_by = st.selectbox(
        "Sort by",
        ["Latest First", "Oldest First", "Longest Distance", "Shortest Distance"],
        key="trip_history_sort_by"
    )
    st.session_state.sort_by = sort_by
with col3:
    search = st.text_input("Search by location", key="trip_history_search")
    st.session_state.search_location = search
st.markdown('</div>', unsafe_allow_html=True)

# Fetch trips
trips = fetch_trips()

# Apply filters
if st.session_state.status_filter != "All":
    trips = [t for t in trips if t["status"].lower() == st.session_state.status_filter.lower()]

if st.session_state.search_location:
    trips = [t for t in trips if 
            st.session_state.search_location.lower() in t["start_location"]["address"].lower() or 
            st.session_state.search_location.lower() in t["end_location"]["address"].lower()]

# Apply sorting
if st.session_state.sort_by == "Latest First":
    trips.sort(key=lambda x: x["created_at"], reverse=True)
elif st.session_state.sort_by == "Oldest First":
    trips.sort(key=lambda x: x["created_at"])
elif st.session_state.sort_by == "Longest Distance":
    trips.sort(key=lambda x: x.get("distance", 0), reverse=True)
elif st.session_state.sort_by == "Shortest Distance":
    trips.sort(key=lambda x: x.get("distance", 0))

# Display trips
if not trips:
    st.info("No trips found.")
else:
    for idx, trip in enumerate(trips):
        st.markdown('<div class="trip-card">', unsafe_allow_html=True)
        
        # Trip Header
        st.markdown(
            f"""
            <div class="trip-header">
                <div class="trip-date">{format_datetime(trip["created_at"])}</div>
                <div class="status-badge status-{trip['status'].lower()}">{trip['status']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Trip Details
        st.markdown('<div class="trip-details">', unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(
                f"""
                <div class="detail-item">
                    <div class="detail-label">Distance</div>
                    <div class="detail-value">{trip.get('distance', 0)/1000:.1f} km</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col2:
            st.markdown(
                f"""
                <div class="detail-item">
                    <div class="detail-label">Duration</div>
                    <div class="detail-value">{trip.get('duration', 0)/60:.0f} mins</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        with col3:
            st.markdown(
                f"""
                <div class="detail-item">
                    <div class="detail-label">Trip ID</div>
                    <div class="detail-value">{trip['_id']}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Locations
        st.markdown(
            f"""
            <div class="location-box">
                <div class="detail-label">Start Location</div>
                <div class="detail-value">{trip['start_location']['address']}</div>
            </div>
            <div class="location-box">
                <div class="detail-label">End Location</div>
                <div class="detail-value">{trip['end_location']['address']}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Map
        st.markdown('<div class="map-container">', unsafe_allow_html=True)
        trip_map = create_trip_map(
            trip["start_location"],
            trip["end_location"],
            trip.get("route", None)
        )
        st_folium(trip_map, width=None, height=200, key=f"map_{idx}")
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Alerts
        if trip.get("detour_alerts") or trip.get("anomaly_alerts"):
            st.markdown('<div class="alert-section">', unsafe_allow_html=True)
            if trip.get("detour_alerts"):
                st.markdown("##### ⚠️ Detour Alerts")
                for alert in trip["detour_alerts"]:
                    st.markdown(f"- {alert}")
            if trip.get("anomaly_alerts"):
                st.markdown("##### 🚨 Anomaly Alerts")
                for alert in trip["anomaly_alerts"]:
                    st.markdown(f"- {alert}")
            st.markdown('</div>', unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True) 