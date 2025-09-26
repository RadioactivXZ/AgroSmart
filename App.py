import streamlit as st
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL of your hosted backend API
BACKEND_URL = "https://agrosmart-flask-backend.onrender.com/"

# --- Custom CSS for Aesthetic Styling ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #f0f8f0, #e0f0e0);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .header-container {
        background: linear-gradient(to right, #2e7d32, #4caf50);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
    }
    .zone-button {
        flex: 1;
        margin: 0 5px;
        padding: 15px 10px;
        border-radius: 15px;
        background: linear-gradient(to bottom, #ffffff, #f5f5f5);
        border: 2px solid #4caf50;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: bold;
        color: #2e7d32;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .zone-button.active {
        background: linear-gradient(to bottom, #4caf50, #2e7d32);
        color: white;
        border-color: #1b5e20;
    }
    .circular-progress {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        position: relative;
        background: conic-gradient(#4caf50 0%, #e0e0e0 0%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    .circular-progress::before {
        content: "";
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: white;
        position: absolute;
    }
    .progress-value {
        position: relative;
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e7d32;
    }
    .progress-label {
        text-align: center;
        margin-top: 10px;
        font-weight: bold;
        color: #555;
    }
    .water-control {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin: 20px 0;
        border-left: 5px solid #4caf50;
    }
    .crop-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #4caf50;
    }
    .notification {
        padding: 10px 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
    .notification.warning {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        color: #e65100;
    }
    .notification.success {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        color: #2e7d32;
    }
    .notification.info {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #0d47a1;
    }
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 30px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. SESSION STATE ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_zone' not in st.session_state:
    st.session_state.current_zone = "Zone 1"
if 'zone_data' not in st.session_state:
    st.session_state.zone_data = {}

# --- 3. API CALL TO BACKEND ---
def fetch_zone_data():
    try:
        res = requests.get(f"{BACKEND_URL}/zones", timeout=5)
        if res.status_code == 200:
            st.session_state.zone_data = res.json()
        else:
            st.error("Failed to fetch data from backend.")
    except Exception as e:
        st.error(f"Error connecting to backend: {e}")

# --- 4. LOGIN PAGE ---
def login_page():
    st.markdown(
        """
        <div class="login-container">
            <h2 style="text-align: center; color: #2e7d32;">🌿 AgroSmart Login</h2>
            <p style="text-align: center; color: #666;">Access your farm dashboard</p>
        </div>
        """, unsafe_allow_html=True
    )
    with st.form("login_form"):
        phone = st.text_input("Phone Number", placeholder="Enter your phone number")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)
        if submit:
            if phone and password:
                st.session_state.logged_in = True
                fetch_zone_data()
                st.rerun()
            else:
                st.error("Please enter both phone number and password")

# --- 5. HOME PAGE ---
def home_page():
    if not st.session_state.zone_data:
        fetch_zone_data()

    st.markdown("<h2>Irrigation Zones</h2>", unsafe_allow_html=True)
    cols = st.columns(4)

    for i, col in enumerate(cols):
        zone_name = f"Zone {i+1}"
        if zone_name not in st.session_state.zone_data:
            continue
        zone_data = st.session_state.zone_data[zone_name]
        button_class = "active" if zone_name == st.session_state.current_zone else ""
        status_color = "#ff9800" if zone_data['water_needed'] else "#4caf50"

        with col:
            if st.button(f"{zone_name}\n{zone_data['status']}", key=zone_name):
                st.session_state.current_zone = zone_name

    st.markdown("---")
    if st.session_state.current_zone not in st.session_state.zone_data:
        st.warning("No data for this zone.")
        return

    zone_data = st.session_state.zone_data[st.session_state.current_zone]
    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown(f"### {st.session_state.current_zone} - {zone_data['crop']}")
        prog_col1, prog_col2, prog_col3 = st.columns(3)

        with prog_col1:
            temp_percent = min(100, (zone_data['temperature'] / 40) * 100)
            st.markdown(f"<div class='circular-progress' style='background: conic-gradient(#ff9800 {temp_percent}%, #e0e0e0 0%);'><div class='progress-value'>{zone_data['temperature']}°C</div></div><div class='progress-label'>Temperature</div>", unsafe_allow_html=True)
        with prog_col2:
            st.markdown(f"<div class='circular-progress' style='background: conic-gradient(#2196f3 {zone_data['humidity']}%, #e0e0e0 0%);'><div class='progress-value'>{zone_data['humidity']}%</div></div><div class='progress-label'>Humidity</div>", unsafe_allow_html=True)
        with prog_col3:
            st.markdown(f"<div class='circular-progress' style='background: conic-gradient(#4caf50 {zone_data['soil_moisture']}%, #e0e0e0 0%);'><div class='progress-value'>{zone_data['soil_moisture']}%</div></div><div class='progress-label'>Soil Moisture</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### Water Control")
        auto_water = st.checkbox("Automatic Watering", value=not zone_data['water_needed'])
        if st.button("💧 Water Now", use_container_width=True):
            try:
                res = requests.post(f"{BACKEND_URL}/zones/{st.session_state.current_zone}/water", json={"auto": auto_water})
                if res.status_code == 200:
                    st.success("Watering action sent successfully!")
                    fetch_zone_data()
                else:
                    st.error("Failed to send watering command.")
            except Exception as e:
                st.error(f"Error sending water command: {e}")

# --- 6. MAIN DASHBOARD ---
def main_dashboard():
    st.markdown("<h1 style='color: #2e7d32;'>🌿 AgroSmart</h1>", unsafe_allow_html=True)
    st.markdown("---")
    home_page()

# --- 7. MAIN APP LOGIC ---
if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()
