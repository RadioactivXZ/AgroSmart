import streamlit as st
import requests
import time

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
st.markdown(
    """
    <style>
    /* (Your full CSS code can be placed here) */
    .stApp {
        background: linear-gradient(to bottom right, #f0f8f0, #e0f0e0);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 30px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
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
    .notification {
        padding: 10px 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
    .notification.warning { background: #fff3e0; border-left: 4px solid #ff9800; color: #e65100; }
    .notification.success { background: #e8f5e9; border-left: 4px solid #4caf50; color: #2e7d32; }
    .notification.info { background: #e3f2fd; border-left: 4px solid #2196f3; color: #0d47a1; }
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
    st.session_state.zone_data = {} # Will be populated by backend call

def fetch_data_from_backend():
    """Function to get the latest data from our FastAPI backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/zones", timeout=30)
        response.raise_for_status()
        live_data = response.json()
        
        for zone, data in live_data.items():
            data.setdefault('target_moisture', 55)
            data.setdefault('water_needed', data.get('soil_moisture', 0) < data['target_moisture'])
            data.setdefault('status', 'Needs Attention' if data['water_needed'] else 'Optimal')
            data.setdefault('manual_water_level', 0)
        
        st.session_state.zone_data = live_data
        st.toast("✅ Live data synced!")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}", icon="🚨")
        return False

def send_manual_water_command(zone_name, water_amount):
    """Send manual watering command to backend."""
    try:
        zone_id = zone_name.split()[-1]  # Extract '1' from 'Zone 1'
        response = requests.post(
            f"{BACKEND_URL}/zones/{zone_id}/water",
            json={"amount": water_amount},
            timeout=10
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send watering command: {e}", icon="🚨")
        return False

# Crop knowledge base
CROP_KNOWLEDGE = {
    'Large Cardamom': { 'temp_range': (18, 28), 'humidity_range': (70, 85), 'water_needs': 'Moderate to high', 'soil_type': 'Well-drained, rich', 'description': "A spice with a strong, smoky flavor.", 'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394&width=1445"},
    'Ginger': { 'temp_range': (20, 30), 'humidity_range': (60, 75), 'water_needs': 'Regular watering', 'soil_type': 'Rich, loamy', 'description': "A rhizome used as a spice and in folk medicine.", 'image_url': "https://organicmandya.com/cdn/shop/files/Ginger.jpg?v=1757079802&width=1000"},
    'Mandarin Orange': { 'temp_range': (22, 32), 'humidity_range': (50, 70), 'water_needs': 'Regular watering', 'soil_type': 'Well-drained, acidic', 'description': "Small, sweet citrus fruits.", 'image_url': "https://www.stylecraze.com/wp-content/uploads/2013/11/845_14-Amazing-Benefits-Of-Mandarin-Oranges-For-Skin-Hair-And-Health_shutterstock_116644108_1200px.jpg.webp"},
}

# --- 3. LOGIN PAGE ---
def login_page():
    st.markdown("<div class='login-container'><h2 style='text-align: center; color: #2e7d32;'>🌿 AgroSmart Login</h2></div>", unsafe_allow_html=True)
    with st.form("login_form"):
        phone = st.text_input("Phone Number", placeholder="Enter your phone number")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        if st.form_submit_button("Login", use_container_width=True):
            if phone and password:
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Please enter both phone number and password")

# --- 4. MAIN DASHBOARD & PAGE ROUTING ---
def main_dashboard():
    col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
    with col1:
        st.markdown("<h1 style='color: #2e7d32;'>🌿 AgroSmart</h1>", unsafe_allow_html=True)
    with col2:
        if st.button("🏠 Home", use_container_width=True): st.session_state.current_page = "home"
    with col3:
        if st.button("🌱 Crops", use_container_width=True): st.session_state.current_page = "crops"
    with col4:
        if st.button("🔔 Notifications", use_container_width=True): st.session_state.current_page = "notifications"
    with col5:
        if st.button("👤 Profile", use_container_width=True): st.session_state.current_page = "profile"
    
    st.markdown("---")
    
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    page_router = {
        "home": home_page,
        "crops": crops_page,
        "notifications": notifications_page,
        "profile": profile_page
    }
    page_router[st.session_state.current_page]()

# --- 5. HOME PAGE ---
def home_page():
    if st.button("🔄 Sync with Live Sensors"):
        with st.spinner("Fetching latest data..."): fetch_data_from_backend()

    st.markdown("<h2>Irrigation Zones</h2>", unsafe_allow_html=True)

    if not st.session_state.zone_data:
        st.warning("Sensor data not loaded. Click 'Sync' or wait for the initial load.")
        return

    def set_current_zone(zone_name):
        st.session_state.current_zone = zone_name

    cols = st.columns(4)
    for i, col in enumerate(cols):
        zone_name = f"Zone {i+1}"
        with col:
            # Add a visual cue to the active button
            button_type = "primary" if st.session_state.current_zone == zone_name else "secondary"
            st.button(zone_name, on_click=set_current_zone, args=(zone_name,), use_container_width=True, type=button_type)

    st.markdown("---")
    
    zone_data = st.session_state.zone_data[st.session_state.current_zone]
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<h3>{st.session_state.current_zone} - {zone_data.get('crop', 'N/A')}</h3>", unsafe_allow_html=True)
        prog_col1, prog_col2, prog_col3 = st.columns(3)
        temp_percent = min(100, (zone_data.get('temperature',0) / 40) * 100)
        prog_col1.markdown(f'<div class="circular-progress" style="background: conic-gradient(#ff9800 {temp_percent}%, #e0e0e0 0%);"><div class="progress-value">{zone_data.get("temperature",0)}°C</div></div><div class="progress-label">Temperature</div>', unsafe_allow_html=True)
        prog_col2.markdown(f'<div class="circular-progress" style="background: conic-gradient(#2196f3 {zone_data.get("humidity",0)}%, #e0e0e0 0%);"><div class="progress-value">{zone_data.get("humidity",0)}%</div></div><div class="progress-label">Humidity</div>', unsafe_allow_html=True)
        prog_col3.markdown(f'<div class="circular-progress" style="background: conic-gradient(#4caf50 {zone_data.get("soil_moisture",0)}%, #e0e0e0 0%);"><div class="progress-value">{zone_data.get("soil_moisture",0)}%</div></div><div class="progress-label">Soil Moisture</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("<h3>Water Control</h3>", unsafe_allow_html=True)
        auto_water = st.checkbox("Automatic Watering", value=not zone_data.get('water_needed', True))
        water_amount = 0
        if not auto_water:
            water_amount = st.slider("Water Amount (Liters)", 0, 100, zone_data.get('manual_water_level', 0))
            st.session_state.zone_data[st.session_state.current_zone]['manual_water_level'] = water_amount
        else:
            # If auto is on, use a default or current level for manual trigger if needed
            water_amount = zone_data.get('manual_water_level', 0)
        
        if st.button("💧 Water Now", use_container_width=True, type="primary"):
            success = send_manual_water_command(st.session_state.current_zone, water_amount)
            if success:
                st.success("Watering command sent to backend! Pump will activate on next sensor sync.")
                # Optionally refresh data
                fetch_data_from_backend()
            else:
                st.error("Failed to send command. Check backend connection.")

# --- 6. CROPS PAGE ---
def crops_page():
    st.markdown("<h2>Crop Information</h2>", unsafe_allow_html=True)
    selected_crop = st.selectbox("Select a crop:", options=list(CROP_KNOWLEDGE.keys()))
    if selected_crop:
        info = CROP_KNOWLEDGE[selected_crop]
        col1, col2 = st.columns([1, 2])
        with col1:
            st.image(info['image_url'], use_container_width=True)
        with col2:
            st.markdown(f"## {selected_crop}")
            st.markdown(f"*Ideal Temp:* {info['temp_range'][0]}°C - {info['temp_range'][1]}°C")
            st.markdown(f"*Ideal Humidity:* {info['humidity_range'][0]}% - {info['humidity_range'][1]}%")

# --- 7. NOTIFICATIONS PAGE ---
def notifications_page():
    st.markdown("<h2>Notifications & Alerts</h2>", unsafe_allow_html=True)
    if not st.session_state.zone_data:
        st.info("No sensor data available to generate notifications.")
        return
    
    has_notifications = False
    for zone, data in st.session_state.zone_data.items():
        if data.get('water_needed'):
            has_notifications = True
            st.markdown(f"<div class='notification warning'>💧 {zone} needs water (Current: {data.get('soil_moisture',0)}%)</div>", unsafe_allow_html=True)
    if not has_notifications:
        st.markdown("<div class='notification success'>🎉 All systems are operating normally!</div>", unsafe_allow_html=True)

# --- 8. PROFILE PAGE ---
def profile_page():
    st.markdown("<h2>Farmer Profile</h2>", unsafe_allow_html=True)
    col1, col2 = st.columns([1, 2])
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
        st.markdown("### Rajesh Kumar")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.pop('initial_load', None)
            st.rerun()
    with col2:
        st.markdown("### Farm Summary")
        if st.session_state.zone_data:
            total_zones = len(st.session_state.zone_data)
            zones_needing_water = sum(1 for data in st.session_state.zone_data.values() if data.get('water_needed'))
            st.metric("Total Zones", total_zones)
            st.metric("Optimal Zones", total_zones - zones_needing_water)
            st.metric("Zones Needing Water", zones_needing_water)

# --- 9. MAIN APP LOGIC ---
if not st.session_state.logged_in:
    login_page()
else:
    if 'initial_load' not in st.session_state:
        with st.spinner("Connecting to farm sensors..."):
            fetch_data_from_backend()
        st.session_state.initial_load = True
    main_dashboard()
