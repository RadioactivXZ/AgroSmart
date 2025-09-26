import streamlit as st
import requests
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide"
)

# --- IMPORTANT: Set this to your deployed Flask backend URL ---
BACKEND_URL = "https://agrosmartback.onrender.com/api/data"

# --- 2. DATA FETCHING ---
def fetch_data_from_backend():
    """Fetches the latest sensor data from the Flask backend."""
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.toast(f"Error from backend: Status Code {response.status_code}", icon="⚠️")
            return None
    except requests.exceptions.RequestException as e:
        st.toast(f"Failed to connect to backend: {e}", icon="❌")
        return None

# --- 3. SESSION STATE INITIALIZATION ---
if 'zone_data' not in st.session_state:
    st.session_state.zone_data = {} # Start with empty data

# --- 4. CROP KNOWLEDGE BASE ---
CROP_KNOWLEDGE = {
    'Large Cardamom': {
        'temp_range': (18, 28), 'humidity_range': (70, 85),
        'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394"
    },
    'Ginger': {
        'temp_range': (20, 30), 'humidity_range': (60, 75),
        'image_url': "https://www.nature-and-garden.com/wp-content/uploads/2021/05/ginger-planting.jpg"
    },
    'Mandarin Orange': {
        'temp_range': (22, 32), 'humidity_range': (50, 70),
        'image_url': "https://www.gardeningknowhow.com/wp-content/uploads/2023/04/mandarin-oranges-on-a-tree.jpg"
    },
    # Default values for when a crop is not assigned
    'Unknown': {
        'temp_range': (0, 100), 'humidity_range': (0, 100), 'image_url': None
    }
}

# --- 5. UI COMPONENTS ---
def home_page():
    st.header("🌿 Real-Time Farm Status")
    
    if not st.session_state.zone_data:
        st.warning("Awaiting first data transmission from sensors. Please wait...")
        st.info("If this message persists, please check if your ESP32 sensors are online and the backend is running.")
        return

    # Dynamically create columns for each zone found in the data
    zones = sorted(st.session_state.zone_data.keys())
    cols = st.columns(len(zones) or 1)

    for i, zone_name in enumerate(zones):
        zone_info = st.session_state.zone_data[zone_name]
        with cols[i]:
            st.subheader(zone_name)
            st.metric("🌡️ Temperature", f"{zone_info.get('temperature', 0):.1f} °C")
            st.metric("💧 Humidity", f"{zone_info.get('humidity', 0):.1f} %")
            st.metric("🌱 Soil Moisture", f"{zone_info.get('soil_moisture', 0):.1f} %")
            
            rain_status = "Raining" if zone_info.get('is_raining') else "Clear"
            pump_status = "ON" if zone_info.get('pump_activated') else "OFF"
            
            st.info(f"Weather: {rain_status} 🌧️" if rain_status == "Raining" else f"Weather: {rain_status} ☀️")
            st.success(f"Pump: {pump_status} 🟢" if pump_status == "ON" else f"Pump: {pump_status} 🔴")
            
            # Display last update time
            timestamp = zone_info.get('timestamp')
            if timestamp:
                st.caption(f"Last updated: {timestamp}")

# --- 6. MAIN APP LOGIC ---
st.title("AgroSmart Monitoring Dashboard")

# --- Sidebar for Refresh Control ---
with st.sidebar:
    st.header("Controls")
    if st.button("🔄 Refresh Data Now"):
        new_data = fetch_data_from_backend()
        if new_data:
            st.session_state.zone_data = new_data
        st.rerun()

    auto_refresh = st.toggle("Auto-refresh every 30s", value=True)


# Fetch new data and update session state
new_data = fetch_data_from_backend()
if new_data:
    st.session_state.zone_data = new_data

# Display the main page
home_page()

# Logic for auto-refresh
if auto_refresh:
    time.sleep(30)
    st.rerun()
