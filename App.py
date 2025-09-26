import streamlit as st
import requests
import time

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide"
)

# --- ❗️ THIS IS THE CORRECTED URL ❗️ ---
BACKEND_URL = "https://agrosmart-flask-backend.onrender.com/api/data"


# --- 2. DATA FETCHING ---
@st.cache_data(ttl=30) # Cache data for 30 seconds
def fetch_data_from_backend():
    """Fetches the latest sensor data from the Flask backend."""
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            # This toast will now show the correct error code if something else goes wrong
            st.toast(f"Error from backend: Status Code {response.status_code}", icon="⚠️")
            return None
    except requests.exceptions.RequestException:
        st.toast(f"Could not connect to backend. Please check the URL.", icon="❌")
        return None

# --- 3. SESSION STATE ---
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Home"

# --- 4. STATIC DATA (for other pages) ---
CROP_KNOWLEDGE = {
    'Large Cardamom': {
        'temp_range': (18, 28), 'humidity_range': (70, 85),
        'description': "A spice with a strong, aromatic flavor thriving in humid climates.",
        'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394"
    },
    'Ginger': {
        'temp_range': (20, 30), 'humidity_range': (60, 75),
        'description': "A flowering plant whose rhizome is widely used as a spice.",
        'image_url': "https://www.nature-and-garden.com/wp-content/uploads/2021/05/ginger-planting.jpg"
    },
    'Mandarin Orange': {
        'temp_range': (22, 32), 'humidity_range': (50, 70),
        'description': "Small, sweet citrus fruits that grow best in warm, sunny climates.",
        'image_url': "https://www.gardeningknowhow.com/wp-content/uploads/2023/04/mandarin-oranges-on-a-tree.jpg"
    }
}

# --- 5. UI PAGES ---
def home_page():
    st.header("🌿 Real-Time Farm Status")
    
    # Data fetching is isolated to this page
    zone_data = fetch_data_from_backend()

    if not zone_data:
        st.warning("Awaiting data from the backend. This could be due to the backend service starting up (it can take a minute on Render) or no sensor data being sent yet.")
        st.info("The dashboard will update automatically. Other pages are still accessible via the sidebar.")
        return

    zones = sorted(zone_data.keys())
    cols = st.columns(len(zones) or 1)

    for i, zone_name in enumerate(zones):
        zone_info = zone_data[zone_name]
        with cols[i]:
            st.subheader(zone_name)
            st.metric("🌡️ Temperature", f"{zone_info.get('temperature', 0):.1f} °C")
            st.metric("💧 Humidity", f"{zone_info.get('humidity', 0):.1f} %")
            st.metric("🌱 Soil Moisture", f"{zone_info.get('soil_moisture', 0):.1f} %")
            rain_status = "Raining 🌧️" if zone_info.get('is_raining') else "Clear ☀️"
            st.metric("Weather", rain_status)

def crops_page():
    st.header("🌱 Crop Knowledge Base")
    selected_crop = st.selectbox("Select a crop", options=CROP_KNOWLEDGE.keys())
    
    if selected_crop:
        info = CROP_KNOWLEDGE[selected_crop]
        col1, col2 = st.columns([1, 2])
        if info.get('image_url'):
            col1.image(info['image_url'], caption=selected_crop)
        col2.subheader(f"Ideal Conditions for {selected_crop}")
        col2.write(f"**Temperature:** {info['temp_range'][0]}°C - {info['temp_range'][1]}°C")
        col2.write(f"**Humidity:** {info['humidity_range'][0]}% - {info['humidity_range'][1]}%")
        col2.write(f"**Description:** {info['description']}")

def profile_page():
    st.header("👤 Farmer Profile")
    st.write("Name: Rajesh Kumar")
    st.write("Location: Sikkim, India")

# --- 6. MAIN APP LAYOUT ---
st.title("AgroSmart Monitoring Dashboard")

# --- Sidebar for Navigation and Controls ---
with st.sidebar:
    st.header("Navigation")
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.current_page = "Home"
    if st.button("🌱 Crops", use_container_width=True):
        st.session_state.current_page = "Crops"
    if st.button("👤 Profile", use_container_width=True):
        st.session_state.current_page = "Profile"
    
    st.divider()
    st.header("Controls")
    auto_refresh = st.toggle("Auto-refresh Home page", value=True)


# --- Page Router ---
if st.session_state.current_page == "Home":
    home_page()
elif st.session_state.current_page == "Crops":
    crops_page()
elif st.session_state.current_page == "Profile":
    profile_page()

# --- Auto-refresh logic (only for home page) ---
if st.session_state.current_page == "Home" and auto_refresh:
    time.sleep(30)
    st.rerun()
