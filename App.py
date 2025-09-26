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

# --- Custom CSS for a more beautiful and interactive look ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    
    html, body, [class*="st-"] {
        font-family: 'Poppins', sans-serif;
    }
    
    .stApp {
        background-color: #F0F2F6;
    }

    .main-header {
        font-size: 3rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 2rem;
        background: -webkit-linear-gradient(45deg, #006400, #55a630);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .card {
        background-color: white;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05);
        margin-bottom: 20px;
        transition: all 0.3s ease;
    }
    
    .card:hover {
        box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        transform: translateY(-5px);
    }
    
    .stMetric {
        border-left: 5px solid #2E8B57;
        padding: 15px;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. DATA & SESSION STATE ---
BACKEND_URL = "https://agrosmart-flask-backend.onrender.com/api/data"

@st.cache_data(ttl=30)
def fetch_data_from_backend():
    try:
        response = requests.get(BACKEND_URL, timeout=10)
        return response.json() if response.status_code == 200 else None
    except requests.exceptions.RequestException:
        return None

# Initialize session state variables
if 'selected_zone' not in st.session_state: st.session_state.selected_zone = "Zone 1"
if 'watering_mode' not in st.session_state: st.session_state.watering_mode = "Auto"
if 'zone_configs' not in st.session_state:
    st.session_state.zone_configs = {f"Zone {i}": {"crop": "Large Cardamom", "target_moisture": 55} for i in range(1, 5)}
if 'daily_water' not in st.session_state or st.session_state.daily_water.get('date') != date.today():
    st.session_state.daily_water = {"date": date.today(), **{f"Zone {i}": 0 for i in range(1, 5)}}

CROP_KNOWLEDGE = {
    'Large Cardamom': {'daily_water_limit_L': 20, 'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394"},
    'Ginger': {'daily_water_limit_L': 15, 'image_url': "https://www.nature-and-garden.com/wp-content/uploads/2021/05/ginger-planting.jpg"},
    'Mandarin Orange': {'daily_water_limit_L': 25, 'image_url': "https://www.gardeningknowhow.com/wp-content/uploads/2023/04/mandarin-oranges-on-a-tree.jpg"}
}

# --- 3. SIDEBAR WITH AUTOSAVE ---
def update_config(zone_key):
    """Callback function to autosave sidebar changes."""
    config = st.session_state.zone_configs[zone_key]
    config['crop'] = st.session_state[f"crop_{zone_key}"]
    config['target_moisture'] = st.session_state[f"moisture_{zone_key}"]

with st.sidebar:
    st.header("⚙️ Zone Configuration")
    st.caption("Changes are saved automatically.")
    for zone in sorted(st.session_state.zone_configs.keys()):
        st.markdown(f"#### {zone}")
        cfg = st.session_state.zone_configs[zone]
        
        st.selectbox(
            "Assign Crop", CROP_KNOWLEDGE.keys(), 
            index=list(CROP_KNOWLEDGE.keys()).index(cfg["crop"]), 
            key=f"crop_{zone}",
            on_change=update_config, args=(zone,)
        )
        st.slider(
            "Target Soil Moisture (%)", 0, 100, 
            value=cfg["target_moisture"], 
            key=f"moisture_{zone}",
            on_change=update_config, args=(zone,)
        )
        st.markdown("---")


# --- 4. MAIN PAGE LAYOUT ---
st.markdown('<h1 class="main-header">🌿 AgroSmart Dashboard 🌿</h1>', unsafe_allow_html=True)

st.session_state.selected_zone = st.radio("Select Zone", [f"Zone {i}" for i in range(1, 5)], horizontal=True)
st.markdown("---")

# Fetch data and configs
live_data = fetch_data_from_backend()
zone_data = live_data.get(st.session_state.selected_zone) if live_data else None
zone_config = st.session_state.zone_configs[st.session_state.selected_zone]
crop_name = zone_config["crop"]
crop_info = CROP_KNOWLEDGE[crop_name]

st.markdown(f"<h2>📍 {st.session_state.selected_zone}: <span style='color:#2E8B57;'>{crop_name}</span></h2>", unsafe_allow_html=True)

col1, col2 = st.columns([2, 1])
with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📊 Live Sensor Readings")
    if not zone_data:
        st.warning("Awaiting live sensor data...")
    else:
        m_cols = st.columns(4)
        m_cols[0].metric("🌡️ Temperature", f"{zone_data.get('temperature', 0):.1f} °C")
        m_cols[1].metric("💧 Humidity", f"{zone_data.get('humidity', 0):.1f} %")
        m_cols[2].metric("🌱 Soil Moisture", f"{zone_data.get('soil_moisture', 0):.1f} %")
        m_cols[3].metric("☀️ Weather", "Raining" if zone_data.get('is_raining') else "Clear")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("💧 Watering Control")
    limit = crop_info['daily_water_limit_L']
    given = st.session_state.daily_water[st.session_state.selected_zone]
    remaining = max(0, limit - given)
    st.progress(given / limit if limit else 0, text=f"{given:.1f} / {limit} L used today")
    
    if remaining <= 0:
        st.success("✅ Daily water limit reached.")
    else:
        # --- Watering Mode Buttons ---
        btn_cols = st.columns(2)
        if btn_cols[0].button("Auto Mode", use_container_width=True, type="primary" if st.session_state.watering_mode == "Auto" else "secondary"):
            st.session_state.watering_mode = "Auto"
        if btn_cols[1].button("Manual Mode", use_container_width=True, type="primary" if st.session_state.watering_mode == "Manual" else "secondary"):
            st.session_state.watering_mode = "Manual"

        amount = 0
        if st.session_state.watering_mode == "Manual":
            amount = st.number_input("Amount (L)", 0.0, remaining, min(1.0, remaining), 0.5)
        else: # Auto mode
            target = zone_config['target_moisture']
            current = zone_data.get('soil_moisture', target) if zone_data else target
            auto_amount = round(max(0, target - current) * 0.5, 1) # Simple formula
            amount = min(auto_amount, remaining)
            st.info(f"Auto-Calculated: {amount} L")

        if st.button("💦 Water Now", use_container_width=True, disabled=(amount<=0)):
            st.session_state.daily_water[st.session_state.selected_zone] += amount
            st.success(f"Watered with {amount} L.")
            time.sleep(1); st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)
