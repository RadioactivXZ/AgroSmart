import streamlit as st
import requests
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide",
)

# URL of your hosted backend API
# For local testing: "http://127.0.0.1:8000"
BACKEND_URL = "https://agrosmartz.streamlit.app/"

# --- Custom CSS for Gradient Background ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to right, #eafaf3, #ffffff); /* Light green to white */
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. SESSION STATE & DATA ---
if 'zone_data' not in st.session_state:
    st.session_state.zone_data = {
        f"Zone {i}": {
            'crop': 'Large Cardamom',
            'target_moisture': 55,
            'soil_moisture': 0, 'temperature': 0, 'humidity': 0,
        } for i in range(1, 5)
    }

# EXPANDED CROP KNOWLEDGE WITH IMAGE URLs AND DESCRIPTIONS
CROP_KNOWLEDGE = {
    'Large Cardamom': {
        'temp_range': (18, 28),
        'humidity_range': (70, 85),
        'description': "Large cardamom is a spice with a strong, aromatic, and smoky flavor. It thrives in humid, subtropical climates with well-drained soil and partial shade. It's often used in Indian and Nepalese cuisine.",
        'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394&width=1445"
    },
    'Ginger': {
        'temp_range': (20, 30),
        'humidity_range': (60, 75),
        'description': "Ginger is a flowering plant whose rhizome (underground stem) is widely used as a spice and folk medicine. It prefers warm, humid climates with rich, moist soil. It's a versatile crop used in cooking, beverages, and traditional remedies.",
        'image_url': "https://organicmandya.com/cdn/shop/files/Ginger.jpg?v=1757079802&width=1000"
    },
    'Mandarin Orange': {
        'temp_range': (22, 32),
        'humidity_range': (50, 70),
        'description': "Mandarin oranges are small, sweet citrus fruits. They grow best in warm, sunny climates with well-drained soil. They are less cold-tolerant than other citrus and require consistent watering during fruit development.",
        'image_url': "https://www.stylecraze.com/wp-content/uploads/2013/11/845_14-Amazing-Benefits-Of-Mandarin-Oranges-For-Skin-Hair-And-Health_shutterstock_116644108_1200px.jpg.webp"
    },
}
CROP_OPTIONS = list(CROP_KNOWLEDGE.keys())

def fetch_data_from_backend():
    """Function to get the latest data from our FastAPI backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/zones")
        response.raise_for_status()
        data = response.json()
        for zone_name, values in data.items():
            # Update only the sensor-specific values
            st.session_state.zone_data[zone_name]['soil_moisture'] = values.get('soil_moisture', 0)
            st.session_state.zone_data[zone_name]['temperature'] = values.get('temperature', 0)
            st.session_state.zone_data[zone_name]['humidity'] = values.get('humidity', 0)
            # You might want to display 'last_updated' as well
        return True
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching data: {e}", icon="🚨")
        return False

# --- 3. HEADER ---
st.title("🌿 AgroSmart Live Dashboard")
st.markdown("Monitor and control your farm's irrigation zones in real-time.")

# --- 4. SIDEBAR SETTINGS ---
with st.sidebar:
    st.header("⚙️ Farm Settings")
    st.subheader("Assign Crop to Each Zone")
    for zone_name, data in st.session_state.zone_data.items():
        data['crop'] = st.selectbox(f"Crop for {zone_name}", options=CROP_OPTIONS, key=f"select_{zone_name}")

    st.markdown("---")
    st.subheader("Set Target Soil Moisture")
    for zone_name, data in st.session_state.zone_data.items():
        data['target_moisture'] = st.slider(f"Target for {zone_name}", 0, 100, data['target_moisture'], key=f"target_{zone_name}")
    
    st.markdown("---")
    if st.button("🔄 Refresh Sensor Data", use_container_width=True):
        with st.spinner("Fetching latest data..."):
            if fetch_data_from_backend():
                st.toast("✅ Data refreshed!")

# --- 5. MAIN DASHBOARD: IRRIGATION ZONES (UPDATED TO USE TABS) ---
st.header("Irrigation Zone Overview")

# Create tabs for each zone
zone_tabs = st.tabs([f"🌿 Zone {i}" for i in range(1, 5)])

for i, tab in enumerate(zone_tabs):
    with tab:
        zone_name = f"Zone {i+1}"
        data = st.session_state.zone_data[zone_name]

        # Display crop details for the selected zone
        st.markdown(f"### Current Crop: {data['crop']}")
        st.markdown(f"**Target Soil Moisture:** {data['target_moisture']}%")

        # Use a container with a border to create a "card" for sensor status
        with st.container(border=True):
            st.markdown("#### Live Sensor Status")
            col1, col2, col3 = st.columns(3)
            # Ensure proper handling of missing data from backend (e.g., during initial load)
            col1.metric("🌡️ Temperature", f"{data.get('temperature', 0):.1f}°C")
            col2.metric("💧 Humidity", f"{data.get('humidity', 0):.1f}%")
            col3.metric("🌱 Soil Moisture", f"{data.get('soil_moisture', 0):.1f}%")

        # Create another card for watering controls
        with st.container(border=True):
            st.markdown("#### Watering Controls")
            c1, c2 = st.columns(2)
            with c1:
                # Placeholder for manual watering button - implement actual API call
                if st.button("💧 Water Manually", key=f"manual_water_{zone_name}", use_container_width=True):
                    st.warning("Manual watering functionality not fully implemented yet!", icon="⚠️")
                    st.success(f"Simulating manual watering command for {zone_name}!")
            with c2:
                # Placeholder for smart watering button
                if st.button("🤖 Smart Water", key=f"smart_water_{zone_name}", use_container_width=True):
                    if data.get('soil_moisture', 0) < data['target_moisture']:
                        st.success(f"Smart Water ON: System will manage watering for {zone_name}.")
                    else:
                        st.info(f"Smart Water OFF: Soil moisture is optimal for {zone_name}.")

# --- 6. CROP KNOWLEDGE BASE (UPDATED WITH IMAGE AND DESCRIPTION) ---
st.markdown("---")
st.header("📚 Crop Knowledge Base")
selected_crop = st.selectbox("Select a crop to learn more:", options=CROP_OPTIONS, index=None, placeholder="Choose a crop...", key="crop_kb_select")

if selected_crop:
    info = CROP_KNOWLEDGE[selected_crop]
    st.subheader(f"Information for {selected_crop}")

    col_img, col_text = st.columns([1, 2]) # Image takes 1/3, text takes 2/3 width

    with col_img:
        st.image(info['image_url'], caption=selected_crop, use_container_width=True)

    with col_text:
        st.write(f"**Ideal Temperature Range:** {info['temp_range'][0]}°C - {info['temp_range'][1]}°C")
        st.write(f"**Ideal Humidity Range:** {info['humidity_range'][0]}% - {info['humidity_range'][1]}%")
        st.write("---")
        st.markdown(f"**Description:** {info['description']}")


# --- Initial Data Fetch on App Load ---
if 'initial_load' not in st.session_state:
    with st.spinner("Connecting to farm sensors..."):
        if fetch_data_from_backend():
            st.toast("✅ Initial data loaded!")
        else:
            st.error("❌ Failed to load initial data.")
    st.session_state.initial_load = True
    st.rerun() # Rerun to display the fetched data
