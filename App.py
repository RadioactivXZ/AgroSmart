import streamlit as st
import requests
import time
from datetime import date

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide"
)

BACKEND_URL = "https://agrosmart-flask-backend.onrender.com/api/data"

# --- 2. DATA FETCHING ---
@st.cache_data(ttl=30)
def fetch_data_from_backend():
    """Fetches data but DOES NOT show UI elements. Safe for caching."""
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None

# --- 3. SESSION STATE INITIALIZATION ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"
if 'selected_zone' not in st.session_state:
    st.session_state.selected_zone = "Zone 1"

# Initialize zone configurations if they don't exist
if 'zone_configs' not in st.session_state:
    st.session_state.zone_configs = {
        "Zone 1": {"crop": "Large Cardamom", "target_moisture": 55},
        "Zone 2": {"crop": "Ginger", "target_moisture": 60},
        "Zone 3": {"crop": "Mandarin Orange", "target_moisture": 50},
        "Zone 4": {"crop": "Large Cardamom", "target_moisture": 55},
    }

# Initialize daily water tracking
if 'daily_water' not in st.session_state or st.session_state.daily_water.get('date') != date.today():
    st.session_state.daily_water = {
        "date": date.today(),
        "Zone 1": 0, "Zone 2": 0, "Zone 3": 0, "Zone 4": 0,
    }


# --- 4. CROP KNOWLEDGE BASE ---
CROP_KNOWLEDGE = {
    'Large Cardamom': {
        'daily_water_limit_L': 20, # Liters per day
        'description': "A spice with a strong, aromatic flavor thriving in humid climates.",
        'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394"
    },
    'Ginger': {
        'daily_water_limit_L': 15,
        'description': "A flowering plant whose rhizome is widely used as a spice.",
        'image_url': "https://www.nature-and-garden.com/wp-content/uploads/2021/05/ginger-planting.jpg"
    },
    'Mandarin Orange': {
        'daily_water_limit_L': 25,
        'description': "Small, sweet citrus fruits that grow best in warm, sunny climates.",
        'image_url': "https://www.gardeningknowhow.com/wp-content/uploads/2023/04/mandarin-oranges-on-a-tree.jpg"
    }
}

# --- 5. UI PAGES ---
def dashboard_page():
    # --- Zone Selector in Main Area ---
    st.subheader("Select a Zone to View")
    zones = ["Zone 1", "Zone 2", "Zone 3", "Zone 4"]
    st.session_state.selected_zone = st.radio(
        "Available Zones", zones, horizontal=True, label_visibility="collapsed"
    )
    st.markdown("---")

    # --- Fetch Live Data ---
    live_data = fetch_data_from_backend()
    selected_zone_data = live_data.get(st.session_state.selected_zone) if live_data else None
    
    # --- Get Zone Configuration ---
    zone_config = st.session_state.zone_configs.get(st.session_state.selected_zone, {})
    crop_name = zone_config.get("crop", "Unknown")
    crop_info = CROP_KNOWLEDGE.get(crop_name, {})
    
    st.header(f"🌿 {st.session_state.selected_zone} - {crop_name}")

    if not selected_zone_data:
        st.warning("Awaiting live sensor data for this zone. Please check sensor and backend status.")
        return

    # --- Main Display Columns ---
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Live Sensor Readings")
        metric_cols = st.columns(4)
        metric_cols[0].metric("🌡️ Temperature", f"{selected_zone_data.get('temperature', 0):.1f} °C")
        metric_cols[1].metric("💧 Humidity", f"{selected_zone_data.get('humidity', 0):.1f} %")
        metric_cols[2].metric("🌱 Soil Moisture", f"{selected_zone_data.get('soil_moisture', 0):.1f} %")
        rain_status = "Raining 🌧️" if selected_zone_data.get('is_raining') else "Clear ☀️"
        metric_cols[3].metric("Weather", rain_status)

    with col2:
        st.subheader("Watering Control")
        water_limit = crop_info.get('daily_water_limit_L', 0)
        water_given_today = st.session_state.daily_water.get(st.session_state.selected_zone, 0)
        water_remaining = max(0, water_limit - water_given_today)

        st.progress(water_given_today / water_limit if water_limit > 0 else 0, text=f"{water_given_today}/{water_limit} L used today")
        
        water_amount = st.number_input("Amount to water (L)", min_value=0.0, max_value=water_remaining, value=min(5.0, water_remaining), step=0.5)

        if st.button("💧 Water Now", use_container_width=True):
            if water_amount > water_remaining:
                st.error(f"Cannot water. Exceeds daily limit of {water_limit} L.")
            else:
                st.session_state.daily_water[st.session_state.selected_zone] += water_amount
                st.success(f"Successfully watered {st.session_state.selected_zone} with {water_amount} L.")
                st.rerun()

def crops_page():
    st.header("🌱 Crop Knowledge Base")
    # Content remains the same as before
    # ...

def profile_page():
    st.header("👤 Farmer Profile")
    # Content remains the same as before
    # ...


# --- 6. MAIN APP LAYOUT ---
# --- Header and Integrated Navigation ---
header_cols = st.columns([3, 1, 1, 1])
with header_cols[0]:
    st.title("AgroSmart Dashboard")

with header_cols[1]:
    if st.button("Dashboard", use_container_width=True, type="primary" if st.session_state.current_page == "Dashboard" else "secondary"):
        st.session_state.current_page = "Dashboard"
        st.rerun()
with header_cols[2]:
    if st.button("Crops", use_container_width=True, type="primary" if st.session_state.current_page == "Crops" else "secondary"):
        st.session_state.current_page = "Crops"
        st.rerun()
with header_cols[3]:
    if st.button("Profile", use_container_width=True, type="primary" if st.session_state.current_page == "Profile" else "secondary"):
        st.session_state.current_page = "Profile"
        st.rerun()

# --- Sidebar for Zone Configuration ---
with st.sidebar:
    st.header("Zone Configuration")
    
    config_zone = st.selectbox("Select Zone to Configure", options=["Zone 1", "Zone 2", "Zone 3", "Zone 4"])
    
    current_config = st.session_state.zone_configs.get(config_zone, {})
    
    # Get the index of the currently assigned crop
    crop_options = list(CROP_KNOWLEDGE.keys())
    current_crop_index = crop_options.index(current_config.get("crop")) if current_config.get("crop") in crop_options else 0
    
    # Assign Crop
    new_crop = st.selectbox(
        "Assign Crop",
        options=crop_options,
        index=current_crop_index,
        key=f"crop_select_{config_zone}"
    )
    
    # Set Target Moisture
    new_moisture = st.slider(
        "Set Target Soil Moisture (%)",
        min_value=0, max_value=100,
        value=current_config.get("target_moisture", 50),
        key=f"moisture_slider_{config_zone}"
    )
    
    if st.button("Save Configuration", use_container_width=True):
        st.session_state.zone_configs[config_zone] = {
            "crop": new_crop,
            "target_moisture": new_moisture
        }
        st.success(f"Configuration saved for {config_zone}.")
        time.sleep(1)
        st.rerun()


# --- Page Router ---
if st.session_state.current_page == "Dashboard":
    dashboard_page()
elif st.session_state.current_page == "Crops":
    crops_page() # You'll need to create or copy this function
elif st.session_state.current_page == "Profile":
    profile_page() # You'll need to create or copy this function
