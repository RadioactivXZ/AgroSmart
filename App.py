import streamlit as st
import requests
import time
from datetime import date

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide"
)

# --- Custom CSS for a modern look ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;600&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        background-color: #F0F2F6;
    }
    
    .card {
        background-color: white;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    
    .stMetric {
        background-color: #F8F9FA;
        border-radius: 8px;
        padding: 10px;
        text-align: center;
    }
    
    h1 {
        color: #006400; /* Dark Green */
    }
</style>
""", unsafe_allow_html=True)


# --- 2. DATA FETCHING & SESSION STATE ---
BACKEND_URL = "https://agrosmart-flask-backend.onrender.com/api/data"

@st.cache_data(ttl=30)
def fetch_data_from_backend():
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"
if 'selected_zone' not in st.session_state:
    st.session_state.selected_zone = "Zone 1"
if 'zone_configs' not in st.session_state:
    st.session_state.zone_configs = {f"Zone {i}": {"crop": "Large Cardamom", "target_moisture": 55} for i in range(1, 5)}
if 'daily_water' not in st.session_state or st.session_state.daily_water.get('date') != date.today():
    st.session_state.daily_water = {"date": date.today(), **{f"Zone {i}": 0 for i in range(1, 5)}}

# --- 3. CROP KNOWLEDGE BASE ---
CROP_KNOWLEDGE = {
    'Large Cardamom': {'daily_water_limit_L': 20, 'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394"},
    'Ginger': {'daily_water_limit_L': 15, 'image_url': "https://www.nature-and-garden.com/wp-content/uploads/2021/05/ginger-planting.jpg"},
    'Mandarin Orange': {'daily_water_limit_L': 25, 'image_url': "https://www.gardeningknowhow.com/wp-content/uploads/2023/04/mandarin-oranges-on-a-tree.jpg"}
}

# --- 4. UI PAGES ---
def dashboard_page():
    # --- Zone Selector ---
    st.subheader("Select a Zone to View")
    zones = [f"Zone {i}" for i in range(1, 5)]
    st.session_state.selected_zone = st.radio("Available Zones", zones, horizontal=True, label_visibility="collapsed")
    st.markdown("---")

    live_data = fetch_data_from_backend()
    selected_zone_data = live_data.get(st.session_state.selected_zone) if live_data else None
    zone_config = st.session_state.zone_configs[st.session_state.selected_zone]
    crop_name = zone_config["crop"]
    crop_info = CROP_KNOWLEDGE[crop_name]

    st.header(f"🌿 {st.session_state.selected_zone} - {crop_name}")

    col1, col2 = st.columns([2, 1])

    with col1:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Live Sensor Readings")
        if not selected_zone_data:
            st.warning("Awaiting live sensor data...")
        else:
            m_cols = st.columns(4)
            m_cols[0].metric("🌡️ Temperature", f"{selected_zone_data.get('temperature', 0):.1f} °C")
            m_cols[1].metric("💧 Humidity", f"{selected_zone_data.get('humidity', 0):.1f} %")
            m_cols[2].metric("🌱 Soil Moisture", f"{selected_zone_data.get('soil_moisture', 0):.1f} %")
            rain = "Raining 🌧️" if selected_zone_data.get('is_raining') else "Clear ☀️"
            m_cols[3].metric("Weather", rain)
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="card">', unsafe_allow_html=True)
        st.subheader("Watering Control")
        water_limit = crop_info['daily_water_limit_L']
        water_given_today = st.session_state.daily_water[st.session_state.selected_zone]
        water_remaining = max(0, water_limit - water_given_today)

        st.progress(water_given_today / water_limit if water_limit else 0, text=f"{water_given_today:.1f} / {water_limit} L used today")
        
        if water_remaining <= 0:
            st.info("Daily water limit reached for this zone.")
        else:
            mode = st.radio("Watering Mode", ["Auto", "Manual"], horizontal=True)
            water_amount = 0
            
            if mode == "Manual":
                water_amount = st.number_input("Amount to water (L)", min_value=0.0, max_value=water_remaining, value=min(1.0, water_remaining), step=0.5)
            else: # Auto mode
                target_moisture = zone_config['target_moisture']
                current_moisture = selected_zone_data.get('soil_moisture', target_moisture) if selected_zone_data else target_moisture
                moisture_deficit = max(0, target_moisture - current_moisture)
                # Simple formula: 0.5 Liters per percentage point of deficit
                auto_amount = round(moisture_deficit * 0.5, 1)
                water_amount = min(auto_amount, water_remaining)
                st.info(f"Recommended amount: {water_amount} L to reach {target_moisture}% moisture.")

            if st.button("💧 Water Now", use_container_width=True, disabled=(water_amount<=0)):
                st.session_state.daily_water[st.session_state.selected_zone] += water_amount
                st.success(f"Watered {st.session_state.selected_zone} with {water_amount} L.")
                time.sleep(1)
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)


def crops_page():
    st.header("🌱 Crop Knowledge Base")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    selected_crop = st.selectbox("Select a crop", options=CROP_KNOWLEDGE.keys())
    if selected_crop:
        info = CROP_KNOWLEDGE[selected_crop]
        col1, col2 = st.columns([1, 2])
        if info.get('image_url'):
            col1.image(info['image_url'], caption=selected_crop)
        col2.subheader(f"Details for {selected_crop}")
        col2.write(f"**Daily Water Limit:** {info['daily_water_limit_L']} Liters")
    st.markdown('</div>', unsafe_allow_html=True)

def profile_page():
    st.header("👤 Farmer Profile")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("**Name:** Rajesh Kumar")
    st.write("**Location:** Sikkim, India")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. MAIN APP LAYOUT & ROUTER ---
header_cols = st.columns([3, 1, 1, 1])
header_cols[0].title("AgroSmart Dashboard")
pages = ["Dashboard", "Crops", "Profile"]
icons = ["🏠", "🌱", "👤"]
for i, page in enumerate(pages):
    if header_cols[i+1].button(f"{icons[i]} {page}", use_container_width=True):
        st.session_state.current_page = page
        st.rerun()

# --- Sidebar for Zone Configuration ---
with st.sidebar:
    st.header("Zone Configuration")
    for zone in sorted(st.session_state.zone_configs.keys()):
        with st.expander(zone):
            config = st.session_state.zone_configs[zone]
            crop_options = list(CROP_KNOWLEDGE.keys())
            current_crop_index = crop_options.index(config["crop"]) if config["crop"] in crop_options else 0
            
            st.selectbox("Assign Crop", options=crop_options, index=current_crop_index, key=f"crop_{zone}")
            st.slider("Set Target Soil Moisture (%)", 0, 100, value=config["target_moisture"], key=f"moisture_{zone}")

    if st.button("Save All Configurations", use_container_width=True):
        for zone in st.session_state.zone_configs.keys():
            st.session_state.zone_configs[zone]['crop'] = st.session_state[f"crop_{zone}"]
            st.session_state.zone_configs[zone]['target_moisture'] = st.session_state[f"moisture_{zone}"]
        st.success("All configurations saved!")
        time.sleep(1)
        st.rerun()

# --- Page Router ---
if st.session_state.current_page == "Dashboard":
    dashboard_page()
elif st.session_state.current_page == "Crops":
    crops_page()
elif st.session_state.current_page == "Profile":
    profile_page()
