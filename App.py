import streamlit as st
import requests
import time
import random

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL of your hosted backend API
BACKEND_URL = "https://agrosmartback.onrender.com" # Ensure no trailing slash

# --- Custom CSS for Aesthetic Styling ---
# (Your CSS remains the same)
st.markdown(
    """
    <style> 
    ... 
    </style>
    """,
    unsafe_allow_html=True
)


# --- 2. SESSION STATE & DATA ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'current_zone' not in st.session_state:
    st.session_state.current_zone = "Zone 1"

if 'zone_data' not in st.session_state:
    # Initialize with empty data; it will be populated from the backend
    st.session_state.zone_data = {}

# --- NEW: Data Fetching Function ---
def fetch_data_from_backend():
    """Function to get the latest data from our FastAPI backend."""
    try:
        # Note: Render free tier may spin down, so the first request might be slow.
        # A timeout of 30 seconds is reasonable.
        response = requests.get(f"{BACKEND_URL}/zones", timeout=30)
        response.raise_for_status() # Raises an exception for bad status codes
        live_data = response.json()
        
        # Update session state with the new live data and add missing keys if needed
        for zone, data in live_data.items():
            data.setdefault('target_moisture', 55)
            data.setdefault('water_needed', data.get('soil_moisture', 0) < 55)
            data.setdefault('status', 'Needs Attention' if data['water_needed'] else 'Optimal')
            data.setdefault('manual_water_level', 0)
        
        st.session_state.zone_data = live_data
        st.toast("✅ Live data synced!")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}", icon="🚨")
        return False

# (Your CROP_KNOWLEDGE dictionary remains the same)
CROP_KNOWLEDGE = { ... }

# --- 3. LOGIN PAGE ---
def login_page():
    # (Your login_page function remains the same)
    st.markdown(...)
    with st.form("login_form"):
        phone = st.text_input("Phone Number", placeholder="Enter your phone number")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)
        if submit:
            if phone and password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Please enter both phone number and password")

# --- 4. MAIN DASHBOARD ---
def main_dashboard():
    # (Your main_dashboard function remains the same)
    col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
    # ... navigation buttons ...
    st.markdown("---")
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    if st.session_state.current_page == "home":
        home_page()
    # ... other page routing ...

# --- 5. HOME PAGE (with Refresh Button) ---
def home_page():
    if st.button("🔄 Sync with Live Sensors"):
        with st.spinner("Fetching latest data..."):
            fetch_data_from_backend()

    st.markdown("<h2>Irrigation Zones</h2>", unsafe_allow_html=True)
    
    # Check if data has been loaded
    if not st.session_state.zone_data:
        st.warning("Sensor data not yet loaded. Click 'Sync' to fetch live data.")
        return

    # ... The rest of your home_page function remains the same, but it will now use live data ...
    # (zone selector, progress bars, etc.)

# (The rest of your page functions: crops_page, notifications_page, profile_page remain the same)
def crops_page():
    # ...
def notifications_page():
    # ...
def profile_page():
    # ...

# (JavaScript section can be removed, see pro-tip below)

# --- 10. MAIN APP LOGIC (with Backend Call) ---
if not st.session_state.logged_in:
    login_page()
else:
    # On first load after login, fetch live data
    if 'initial_load' not in st.session_state:
        with st.spinner("Connecting to farm sensors..."):
            fetch_data_from_backend()
        st.session_state.initial_load = True

    main_dashboard()
