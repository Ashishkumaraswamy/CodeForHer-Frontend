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
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: bold;
        font-size: 1.1rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        background-color: #FF6B6B;
        transform: translateY(-2px);
        box-shadow: 0 6px 8px rgba(0, 0, 0, 0.2);
    }
    .stButton>button:active {
        transform: translateY(0);
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
    .error-message {
        background-color: #FFE5E5;
        border-left: 4px solid #FF4B4B;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
        color: #D32F2F;
    }
    .success-message {
        background-color: #E8F5E9;
        border-left: 4px solid #4CAF50;
        padding: 10px;
        margin: 10px 0;
        border-radius: 4px;
        color: #2E7D32;
    }
    </style>
""", unsafe_allow_html=True)

# Display header with logo
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image("codeforher_frontend/static/images/logo.jpeg", width=200)
    st.title("Guardian Lane 🚦")
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
        if not login_email or not login_password:
            st.markdown(
                '<div class="error-message">⚠️ Please enter both email and password</div>',
                unsafe_allow_html=True
            )
        else:
            try:
                response = requests.post(
                    f"{BASE_URL}/auth/login",
                    json={"email": login_email, "password": login_password}
                )
                
                if response.status_code == 200:
                    st.markdown(
                        '<div class="success-message">✅ Login successful!</div>',
                        unsafe_allow_html=True
                    )
                    st.session_state["token"] = response.json()
                    switch_page("Trip_Planner")
                elif response.status_code == 401:
                    st.markdown(
                        '<div class="error-message">❌ Invalid email or password. Please check your credentials.</div>',
                        unsafe_allow_html=True
                    )
                elif response.status_code == 404:
                    st.markdown(
                        '<div class="error-message">❌ Account not found. Please sign up first.</div>',
                        unsafe_allow_html=True
                    )
                else:
                    error_detail = response.json().get("detail", "Unknown error occurred")
                    st.markdown(
                        f'<div class="error-message">❌ Login failed: {error_detail}</div>',
                        unsafe_allow_html=True
                    )
            except requests.exceptions.ConnectionError:
                st.markdown(
                    '<div class="error-message">❌ Unable to connect to server. Please check your internet connection.</div>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.markdown(
                    f'<div class="error-message">❌ An unexpected error occurred: {str(e)}</div>',
                    unsafe_allow_html=True
                )

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
        # Check each required field individually
        missing_fields = []
        
        if not name:
            missing_fields.append("Full Name")
        if not email:
            missing_fields.append("Email")
        if not phone:
            missing_fields.append("Phone")
        if not password:
            missing_fields.append("Password")
        if not home_address:
            missing_fields.append("Home Address")
            
        # Check emergency contacts
        if not emergency_contacts:
            missing_fields.append("At least one Emergency Contact")
        else:
            for i, contact in enumerate(emergency_contacts):
                if not contact.get("name"):
                    missing_fields.append(f"Emergency Contact {i+1} Name")
                if not contact.get("phone"):
                    missing_fields.append(f"Emergency Contact {i+1} Phone")
                if not contact.get("relationship"):
                    missing_fields.append(f"Emergency Contact {i+1} Relationship")

        if missing_fields:
            st.markdown(
                f'<div class="error-message">⚠️ Please fill in the following required fields:<br>' + 
                '<br>'.join(f"- {field}" for field in missing_fields) + '</div>',
                unsafe_allow_html=True
            )
        else:
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
                    st.markdown(
                        '<div class="success-message">✅ Signup successful! You can now login.</div>',
                        unsafe_allow_html=True
                    )
                    st.session_state["show_login"] = True
                else:
                    error_message = response.json().get("detail", "Unknown error occurred")
                    st.markdown(
                        f'<div class="error-message">❌ Signup failed: {error_message}</div>',
                        unsafe_allow_html=True
                    )
            except requests.exceptions.ConnectionError:
                st.markdown(
                    '<div class="error-message">❌ Unable to connect to server. Please check your internet connection.</div>',
                    unsafe_allow_html=True
                )
            except Exception as e:
                st.markdown(
                    f'<div class="error-message">❌ An unexpected error occurred: {str(e)}</div>',
                    unsafe_allow_html=True
                )
