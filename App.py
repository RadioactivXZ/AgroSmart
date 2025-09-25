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
    .notification {
        padding: 10px 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
    .notification.warning { background: #fff3e0; border-left: 4px solid #ff9800; color: #e65100; }
    .notification.success { background: #e8f5e9; border-left: 4px solid #4caf50; color: #2e7d32; }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. SESSION STATE & DATA ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_zone' not in st.session_state:
    st.session_state.current_zone = "Zone 1"
if 'current_page' not in st.session_state:
    st.session_state.current_page = "home"
if 'last_fetch' not in st.session_state:
    st.session_state.last_fetch = 0

# Initialize zone_data with frontend-specific settings
if 'zone_data' not in st.session_state:
    st.session_state.zone_data = {
        f"Zone {i}": {
            'crop': 'Large Cardamom', # User-configurable setting
            'target_moisture': 55,     # User-configurable setting
            'soil_moisture': 0,        # Fetched from backend
            'temperature': 0,          # Fetched from backend
            'humidity': 0,             # Fetched from backend
            'manual_water_level': 10,  # User-configurable setting
            'water_needed': False,     # Calculated from fetched data
            'status': "Unknown"        # Calculated from fetched data
        } for i in range(1, 5)
    }

def fetch_data_from_backend():
    """Function to get the latest data from our FastAPI backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/zones", timeout=30)
        response.raise_for_status()
        live_data = response.json()
        
        # --- CRITICAL FIX ---
        # Instead of replacing zone_data, update it to preserve user settings.
        for zone, data in live_data.items():
            if zone in st.session_state.zone_data:
                # Update only the sensor readings
                st.session_state.zone_data[zone]['soil_moisture'] = data.get('soil_moisture', 0)
                st.session_state.zone_data[zone]['temperature'] = data.get('temperature', 0)
                st.session_state.zone_data[zone]['humidity'] = data.get('humidity', 0)
                
                # Recalculate status based on new data
                target = st.session_state.zone_data[zone].get('target_moisture', 55)
                is_needed = data.get('soil_moisture', 0) < target
                st.session_state.zone_data[zone]['water_needed'] = is_needed
                st.session_state.zone_data[zone]['status'] = 'Needs Water' if is_needed else 'Optimal'

        st.session_state.last_fetch = time.time()
        st.toast("✅ Live data synced!")
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Could not connect to backend: {e}", icon="🚨")
        return False

# Crop knowledge base
CROP_KNOWLEDGE = {
    'Large Cardamom': { 'temp_range': (18, 28), 'humidity_range': (70, 85), 'description': "A spice with a strong, smoky flavor.", 'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394&width=1445"},
    'Ginger': { 'temp_range': (20, 30), 'humidity_range': (60, 75), 'description': "A rhizome used as a spice and in folk medicine.", 'image_url': "https://organicmandya.com/cdn/shop/files/Ginger.jpg?v=1757079802&width=1000"},
    'Mandarin Orange': { 'temp_range': (22, 32), 'humidity_range': (50, 70), 'description': "Small, sweet citrus fruits.", 'image_url': "https://www.stylecraze.com/wp-content/uploads/2013/11/845_14-Amazing-Benefits-Of-Mandarin-Oranges-For-Skin-Hair-And-Health_shutterstock_116644108_1200px.jpg.webp"},
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
    # Auto-refresh logic
    if time.time() - st.session_state.last_fetch > 30:
        fetch_data_from_backend()

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
    
    page_router = {"home": home_page, "crops": crops_page, "notifications": notifications_page, "profile": profile_page}
    page_router[st.session_state.current_page]()

# --- 5. HOME PAGE ---
def home_page():
    if st.button("🔄 Sync with Live Sensors"):
        with st.spinner("Fetching latest data..."): fetch_data_from_backend()

    st.markdown("<h2>Irrigation Zones</h2>", unsafe_allow_html=True)

    if not st.session_state.zone_data:
        st.warning("Sensor data not loaded. Click 'Sync' to fetch live data.")
        return

    def set_current_zone(zone_name):
        st.session_state.current_zone = zone_name

    cols = st.columns(4)
    for i, col in enumerate(cols):
        zone_name = f"Zone {i+1}"
        with col:
            button_type = "primary" if st.session_state.current_zone == zone_name else "secondary"
            st.button(zone_name, on_click=set_current_zone, args=(zone_name,), use_container_width=True, type=button_type)

    st.markdown("---")
    
    zone_data = st.session_state.zone_data[st.session_state.current_zone]
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"<h3>{st.session_state.current_zone} - {zone_data.get('crop', 'N/A')}</h3>", unsafe_allow_html=True)
        prog_col1, prog_col2, prog_col3 = st.columns(3)
        temp_percent = min(100, (zone_data.get('temperature',0) / 40) * 100)
        prog_col1.markdown(f'<div class="circular-progress" style="background: conic-gradient(#ff9800 {temp_percent}%, #e0e0e0 0%);"><div class="progress-value">{zone_data.get("temperature",0):.1f}°C</div></div><div class="progress-label">Temperature</div>', unsafe_allow_html=True)
        prog_col2.markdown(f'<div class="circular-progress" style="background: conic-gradient(#2196f3 {zone_data.get("humidity",0)}%, #e0e0e0 0%);"><div class="progress-value">{zone_data.get("humidity",0):.1f}%</div></div><div class="progress-label">Humidity</div>', unsafe_allow_html=True)
        prog_col3.markdown(f'<div class="circular-progress" style="background: conic-gradient(#4caf50 {zone_data.get("soil_moisture",0)}%, #e0e0e0 0%);"><div class="progress-value">{zone_data.get("soil_moisture",0):.1f}%</div></div><div class="progress-label">Soil Moisture</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("<h3>Water Control</h3>", unsafe_allow_html=True)
        auto_water = st.checkbox("Automatic Watering", value=not zone_data.get('water_needed', True))
        if not auto_water:
            water_amount = st.slider("Water Amount (Liters)", 0, 100, zone_data.get('manual_water_level', 0))
            st.session_state.zone_data[st.session_state.current_zone]['manual_water_level'] = water_amount
        
        # --- IMPLEMENTED API CALL ---
        if st.button("💧 Water Now", use_container_width=True, type="primary"):
            zone_id = st.session_state.current_zone.split(" ")[1]
            try:
                with st.spinner("Sending command..."):
                    response = requests.post(f"{BACKEND_URL}/manual_water/{zone_id}", timeout=10)
                    response.raise_for_status()
                    st.success(f"Watering command sent to Zone {zone_id}!")
                    time.sleep(2) # Give user time to see success message
                    st.rerun()
            except requests.exceptions.RequestException as e:
                st.error(f"Failed to send command: {e}")

# --- 6. CROPS PAGE ---
def crops_page():
    st.markdown("<h2>Crop Management</h2>", unsafe_allow_html=True)
    for zone_name, data in st.session_state.zone_data.items():
        with st.expander(f"Configure {zone_name} (Current: {data['crop']})"):
            new_crop = st.selectbox("Select new crop:", options=list(CROP_KNOWLEDGE.keys()), key=f"crop_{zone_name}", index=list(CROP_KNOWLEDGE.keys()).index(data['crop']))
            new_target = st.slider("Set target soil moisture:", 0, 100, data['target_moisture'], key=f"target_{zone_name}")
            
            if new_crop != data['crop']:
                st.session_state.zone_data[zone_name]['crop'] = new_crop
                st.rerun()
            if new_target != data['target_moisture']:
                st.session_state.zone_data[zone_name]['target_moisture'] = new_target
                st.rerun()

# --- 7. NOTIFICATIONS PAGE ---
def notifications_page():
    st.markdown("<h2>Notifications & Alerts</h2>", unsafe_allow_html=True)
    if not st.session_state.zone_data:
        st.info("No sensor data available.")
        return
    
    has_notifications = False
    for zone, data in st.session_state.zone_data.items():
        if data.get('water_needed'):
            has_notifications = True
            st.markdown(f"<div class='notification warning'>💧 {zone} needs water (Current: {data.get('soil_moisture',0):.1f}%)</div>", unsafe_allow_html=True)
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
            st.session_state.clear() # Clear all session data on logout
            st.rerun()
    with col2:
        st.markdown("### Farm Summary")
        if st.session_state.zone_data:
            total_zones = len(st.session_state.zone_data)
            zones_needing_water = sum(1 for data in st.session_state.zone_data.values() if data.get('water_needed'))
            st.metric("Total Zones", total_zones)
            st.metric("Optimal Zones", total_zones - zones_needing_water)
            st.metric("Zones Needing Water", zones_needing_water, delta_color="inverse")

# --- 9. MAIN APP LOGIC ---
if not st.session_state.logged_in:
    login_page()
else:
    if 'initial_load' not in st.session_state:
        with st.spinner("Connecting to farm sensors..."):
            fetch_data_from_backend()
        st.session_state.initial_load = True
    main_dashboard()
