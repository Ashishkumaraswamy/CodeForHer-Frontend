import streamlit as st
import requests
import datetime
from streamlit_extras.switch_page_button import switch_page

# Base URL of your FastAPI backend
BASE_URL = "http://localhost:8080/api"  # Replace with the actual backend URL

# Streamlit layout setup
st.set_page_config(
    page_title="Women Commute Safety - Login & Signup",
    layout="wide",
    initial_sidebar_state="collapsed"
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
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
        justify-content: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 60px;
        white-space: pre-wrap;
        font-size: 1.2rem;
        padding: 0 2rem;
        background-color: #f0f2f6;
        border-radius: 5px;
        transition: all 0.3s ease;
    }
    .stTabs [aria-selected="true"] {
        background-color: #FF4B4B;
        color: white;
        border-radius: 5px;
        font-weight: bold;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stTextInput>div>div>input {
        border-radius: 5px;
    }
    .stTextArea>div>div>textarea {
        border-radius: 5px;
    }
    </style>
""", unsafe_allow_html=True)

# Display header with logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("codeforher_frontend/static/images/logo.jpeg", width=200)
    st.title("Women Commute Safety 🚦")
    st.markdown("### Welcome! Please login or signup to continue")

# Create tabs for Login and Signup with more spacing
st.markdown("<br>", unsafe_allow_html=True)  # Add some space before tabs
tab1, tab2 = st.tabs(["🔐 Login", "📝 Signup"])

# ----------- LOGIN SECTION -----------
with tab1:
    st.markdown("### Login to your account")
    login_email = st.text_input("Email", placeholder="Enter your email", key="login_email")
    login_password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")

    if st.button("Login", key="login_button"):
        if login_email and login_password:
            try:
                response = requests.post(
                    f"{BASE_URL}/auth/login",
                    json={"email": login_email, "password": login_password}
                )
                if response.status_code == 200:
                    st.success("✅ Login successful!")
                    st.session_state["token"] = response.json()
                    switch_page("Trip_Planner")
                else:
                    st.error("❌ Invalid credentials. Please try again.")
            except Exception as e:
                st.error(f"Error connecting to server: {e}")
        else:
            st.warning("⚠️ Please fill in all fields")

# ----------- SIGNUP SECTION -----------
with tab2:
    st.markdown("### Create a new account")
    
    # Personal Information
    st.subheader("Personal Information")
    name = st.text_input("Full Name", placeholder="Enter your full name")
    email = st.text_input("Email", placeholder="Enter a valid email")
    phone = st.text_input("Phone", placeholder="+91-XXXXXXXXXX")
    password = st.text_input("Password", type="password", placeholder="Create a password")
    home_address = st.text_area("Home Address", placeholder="Enter your home address")

    if home_address:
        response = requests.post(f"{BASE_URL}/maps/get-latitude-longitude", json={"address": home_address})
        latitude, longitude = response.json().get("latitude"), response.json().get("longitude")

    # Emergency contacts
    st.subheader("Emergency Contacts")
    emergency_contacts = []
    for i in range(2):
        col1, col2, col3 = st.columns(3)
        with col1:
            contact_name = st.text_input(f"Contact {i + 1} Name", key=f"contact_name_{i}")
        with col2:
            contact_phone = st.text_input(f"Contact {i + 1} Phone", key=f"contact_phone_{i}")
        with col3:
            contact_relation = st.text_input(f"Contact {i + 1} Relation", key=f"contact_relation_{i}")
        if contact_name and contact_phone:
            emergency_contacts.append({
                "name": contact_name,
                "phone": contact_phone,
                "relationship": contact_relation
            })

    # Preferences
    st.subheader("Safety Preferences")
    col1, col2 = st.columns(2)
    with col1:
        location_sharing = st.checkbox("Enable Location Sharing", value=True)
        SOS_active = st.checkbox("Enable SOS Alerts", value=True)
    with col2:
        safe_radius = st.number_input("Safe Radius (meters)", min_value=50, max_value=1000, value=100)
        voice_assist = st.checkbox("Enable Voice Assist", value=True)

    if st.button("Signup", key="signup_button"):
        if name and email and phone and password and home_address and emergency_contacts:
            signup_data = {
                "name": name,
                "email": email,
                "phone": phone,
                "home_address": home_address,
                "password": password,
                "emergency_contacts": emergency_contacts,
                "preferences": {
                    "location_sharing": location_sharing,
                    "SOS_active": SOS_active,
                    "safe_radius": safe_radius,
                    "voice_assist": voice_assist
                },
                "created_at": datetime.datetime.now().isoformat(),
                "updated_at": datetime.datetime.now().isoformat()
            }

            try:
                response = requests.post(f"{BASE_URL}/auth/signup", json=signup_data)
                if response.status_code == 200:
                    st.success("✅ Signup successful! You can now login.")
                    st.session_state["show_login"] = True
                else:
                    st.error("❌ Signup failed. Please try again.")
            except Exception as e:
                st.error(f"Error connecting to server: {e}")
        else:
            st.warning("⚠️ Please fill in all required fields")
