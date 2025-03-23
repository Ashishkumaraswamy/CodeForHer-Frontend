import streamlit as st
import requests
import folium
from streamlit_folium import st_folium
from streamlit_extras.switch_page_button import switch_page
import time
import polyline
import asyncio
import aiohttp
from datetime import datetime, timedelta
from typing import List
from pydantic import BaseModel

# Base URL of your FastAPI backend
BASE_URL = "http://localhost:8080/api"

# Page config
st.set_page_config(
    page_title="Trip Planner",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
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
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .map-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .trip-details {
        background-color: #f8f9fa;
        padding: 20px;
        border-radius: 10px;
        margin-top: 20px;
    }
    .directions-container {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        overflow-y: auto;
    }
    .direction-step {
        padding: 10px;
        border-bottom: 1px solid #eee;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    .direction-step:last-child {
        border-bottom: none;
    }
    .step-number {
        background-color: #FF4B4B;
        color: white;
        width: 25px;
        height: 25px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: bold;
    }
    .step-content {
        flex-grow: 1;
    }
    .step-distance {
        color: #666;
        font-size: 0.9em;
    }
    .safety-card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    .safety-header {
        color: #333;
        font-size: 1.1em;
        font-weight: 600;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 8px;
    }
    .safety-content {
        color: #555;
        font-size: 0.95em;
        line-height: 1.5;
    }
    .time-badge {
        background-color: #FF4B4B;
        color: white;
        padding: 4px 12px;
        border-radius: 15px;
        font-size: 0.85em;
        font-weight: 500;
    }
    .road-name {
        font-weight: 500;
        color: #333;
    }
    </style>
""", unsafe_allow_html=True)

# Check if user is logged in
if "token" not in st.session_state:
    st.warning("Please login to access the trip planner.")
    switch_page("Login")
    st.stop()

# Initialize session state for trip details
if "trip_details" not in st.session_state:
    st.session_state.trip_details = None
if "route_map" not in st.session_state:
    st.session_state.route_map = None
if "is_trip_started" not in st.session_state:
    st.session_state.is_trip_started = False
if "route_steps" not in st.session_state:
    st.session_state.route_steps = None

# Verify token structure
if not isinstance(st.session_state.token, dict) or "user_id" not in st.session_state.token:
    st.error("Invalid authentication. Please login again.")
    st.session_state.clear()
    switch_page("Login")
    st.stop()

# Header
st.title("🚗 Trip Planner")
st.markdown("Plan your safe commute journey")

# Location Input Section
st.subheader("Enter Trip Details")
col1, col2 = st.columns(2)

with col1:
    source = st.text_input("Start Location", placeholder="Enter starting point", key="source")
with col2:
    destination = st.text_input("End Location", placeholder="Enter destination", key="destination")

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_coordinates(address):
    """Cache the geocoding API calls"""
    response = requests.post(f"{BASE_URL}/maps/get-latitude-longitude", json={"address": address})
    if response.status_code == 200:
        return response.json()
    return None

async def fetch_route_data(session, url, payload):
    """Async function to fetch route data"""
    async with session.post(url, json=payload) as response:
        return await response.json()

async def fetch_all_route_data(source_coords, dest_coords):
    """Async function to fetch all route data"""
    async with aiohttp.ClientSession() as session:
        payload = {
            "origin": {
                "latitude": source_coords["latitude"],
                "longitude": source_coords["longitude"],
                "address": source
            },
            "destination": {
                "latitude": dest_coords["latitude"],
                "longitude": dest_coords["longitude"],
                "address": destination
            }
        }
        
        tasks = [
            fetch_route_data(session, f"{BASE_URL}/maps/get-time-distance", payload),
            fetch_route_data(session, f"{BASE_URL}/maps/get-route", payload)
        ]
        
        results = await asyncio.gather(*tasks)
        return results

@st.cache_data(ttl=3600)  # Cache for 1 hour
def fetch_route_details():
    """Cache the complete route details"""
    if source and destination:
        try:
            source_coords = get_coordinates(source)
            dest_coords = get_coordinates(destination)
            
            if source_coords and dest_coords:
                # Run async function and get results
                route_data, route_steps = asyncio.run(fetch_all_route_data(source_coords, dest_coords))
                
                if route_data and route_steps:
                    route_data["origin"] = source_coords
                    route_data["destination"] = dest_coords
                    return route_data, route_steps
        except Exception as e:
            st.error(f"Error fetching route details: {e}")
    return None, None

@st.cache_data(ttl=3600)  # Cache for 1 hour
def create_map(route_data):
    """Cache the map creation"""
    m = folium.Map(
        location=[route_data["origin"]["latitude"], route_data["origin"]["longitude"]],
        zoom_start=13
    )
    
    folium.Marker(
        [route_data["origin"]["latitude"], route_data["origin"]["longitude"]],
        popup="Start",
        icon=folium.Icon(color='green', icon='info-sign')
    ).add_to(m)
    
    folium.Marker(
        [route_data["destination"]["latitude"], route_data["destination"]["longitude"]],
        popup="End",
        icon=folium.Icon(color='red', icon='info-sign')
    ).add_to(m)
    
    try:
        route_coordinates = polyline.decode(route_data["route"])
        folium.PolyLine(
            route_coordinates,
            weight=3,
            color='blue',
            opacity=0.8
        ).add_to(m)
    except Exception as e:
        st.error(f"Error rendering route: {e}")
    
    return m

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_route_safety_insights(steps):
    """Cache the safety insights API calls"""
    try:
        # Format steps according to RouteStep model
        formatted_steps = [
            RouteStep(
                instructions=step['instructions'],
                distance=step['readable_distance'],
                duration=step['readable_duration']
            ).model_dump()
            for step in steps
        ]
        
        # Create request payload using RouteSafetyRequest model
        request_payload = RouteSafetyRequest(route_steps=formatted_steps).model_dump()
        
        response = requests.post(
            f"{BASE_URL}/llm/route-safety",
            json=request_payload,
            headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
        )
        if response.status_code == 200:
            return response.json()
        return None
    except Exception as e:
        st.error(f"Error getting safety insights: {e}")
        return None

# Function to display route steps
def display_route_steps(route_steps):
    if route_steps and "routes" in route_steps and route_steps["routes"]:
        steps = route_steps["routes"][0]["legs"][0]["steps"]
        st.markdown("### Turn-by-Turn Directions")
        st.markdown('<div class="directions-container">', unsafe_allow_html=True)
        
        for i, step in enumerate(steps, 1):
            st.markdown(f"""
                <div class="direction-step">
                    <div class="step-number">{i}</div>
                    <div class="step-content">
                        <div>{step['instructions']}</div>
                        <div class="step-distance">{step['readable_distance']} • {step['readable_duration']}</div>
                    </div>
                </div>
            """, unsafe_allow_html=True)
        
        st.markdown('</div>', unsafe_allow_html=True)

# Add these model classes after the imports
class RouteStep(BaseModel):
    instructions: str
    distance: str
    duration: str

class RouteSafetyRequest(BaseModel):
    route_steps: List[RouteStep]

# Add this function to display safety insights
def display_safety_insights(safety_data):
    st.markdown("### 🛡️ Trip Safety Insights")
    
    # General Insights
    st.markdown('<div class="safety-card">', unsafe_allow_html=True)
    st.markdown('<div class="safety-header">📍 Route Overview</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="safety-content">{safety_data["general_insights"]}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Safety Tips by Time
    st.markdown('<div class="safety-card">', unsafe_allow_html=True)
    st.markdown('<div class="safety-header">⏰ Time-based Safety Tips</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    times = list(safety_data["safety_tips"].items())
    for i, (time, tip) in enumerate(times):
        with cols[i % 2]:
            st.markdown(f'<div style="margin-bottom: 1rem;">', unsafe_allow_html=True)
            st.markdown(f'<span class="time-badge">{time.upper()}</span>', unsafe_allow_html=True)
            st.markdown(f'<div class="safety-content" style="margin-top: 0.5rem;">{tip}</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Road Conditions
    st.markdown('<div class="safety-card">', unsafe_allow_html=True)
    st.markdown('<div class="safety-header">🛣️ Road Conditions</div>', unsafe_allow_html=True)
    for road, condition in safety_data["road_conditions"].items():
        st.markdown(f'<div style="margin-bottom: 0.8rem;">', unsafe_allow_html=True)
        st.markdown(f'<span class="road-name">{road}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="safety-content">{condition}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Areas of Concern
    st.markdown('<div class="safety-card">', unsafe_allow_html=True)
    st.markdown('<div class="safety-header">⚠️ Areas of Concern</div>', unsafe_allow_html=True)
    for area, concern in safety_data["areas_of_concern"].items():
        st.markdown(f'<div style="margin-bottom: 0.8rem;">', unsafe_allow_html=True)
        st.markdown(f'<span class="road-name">{area}</span>', unsafe_allow_html=True)
        st.markdown(f'<div class="safety-content">{concern}</div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

# Fetch and display route details when both locations are entered
if source and destination:
    with st.spinner("Fetching route details..."):
        route_data, route_steps = fetch_route_details()
        if route_data:
            st.session_state.trip_details = route_data
            st.session_state.route_steps = route_steps
            
            # Display trip details
            st.markdown("### Trip Details")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Distance", f"{route_data['distance']/1000:.1f} km")  # Convert meters to km
            with col2:
                st.metric("Duration", f"{route_data['duration']/60:.0f} mins")  # Convert seconds to minutes
            with col3:
                st.metric("Estimated Arrival", time.strftime("%I:%M %p", time.localtime(time.time() + route_data['duration'])))
            

            
            r1c1, r1c2 = st.columns([4,3])
            with r1c1:
                # Display map and directions side by side
                st.markdown("### Route Map")
                st.session_state.route_map = create_map(route_data)
                with st.container():
                    st.markdown('<div class="map-container">', unsafe_allow_html=True)
                    st_folium(st.session_state.route_map, width=800, height=400)
                st.markdown('</div>', unsafe_allow_html=True)
                
                
            
            with r1c2:
                display_route_steps(route_steps)
            
            # Add Safety Insights Section
            if route_steps and "routes" in route_steps and route_steps["routes"]:
                steps = route_steps["routes"][0]["legs"][0]["steps"]
                safety_insights = get_route_safety_insights(steps)
                if safety_insights:
                    display_safety_insights(safety_insights)
            
            # Start Trip Button
            if not st.session_state.is_trip_started:
                if st.button("Start Trip", key="start_trip", type="primary"):
                    try:
                        if not isinstance(st.session_state.token, dict) or "user_id" not in st.session_state.token:
                            st.error("Authentication error. Please login again.")
                            st.session_state.clear()
                            switch_page("Login")
                            st.stop()

                        start_location = route_data["origin"]
                        start_location["address"] = source
                        end_location = route_data["destination"]
                        end_location["address"] = destination

                        # Call backend to start trip
                        response = requests.post(
                            f"{BASE_URL}/commute/start-trip",
                            json={
                                "user_id": st.session_state.token["user_id"],
                                "start_location": start_location,
                                "end_location": end_location,
                                "distance": route_data["distance"],
                                "duration": route_data["duration"]
                            },
                            headers={"Authorization": f"Bearer {st.session_state.token['access_token']}"}
                        )
                        
                        if response.status_code == 200:
                            trip_data = response.json()
                            st.session_state.is_trip_started = True
                            st.session_state.trip_id = trip_data["trip_id"]  # Store trip_id in session state
                            st.success("Trip started successfully!")
                            time.sleep(2)
                            switch_page("Active_Trip")
                        else:
                            st.error("❌ Failed to start trip. Please try again.")
                    except Exception as e:
                        st.error(f"Error starting trip: {e}")
                        st.error("Please try logging in again.")
                        st.session_state.clear()
                        switch_page("Login")
        else:
            st.error("❌ Could not find route between these locations. Please try different locations.") 