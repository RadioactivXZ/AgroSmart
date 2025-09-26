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

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@400;600;700&display=swap');
    html, body, [class*="st-"] { font-family: 'Poppins', sans-serif; }
    .stApp { background-color: #F0F2F6; }
    .main-header {
        font-size: 2.5rem; font-weight: 700; text-align: left;
        background: -webkit-linear-gradient(45deg, #006400, #55a630);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    .card {
        background-color: white; border-radius: 15px; padding: 25px;
        box-shadow: 0 10px 20px rgba(0,0,0,0.05); margin-bottom: 20px;
    }
    .stMetric { border-left: 5px solid #2E8B57; padding: 15px; }
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
if 'current_page' not in st.session_state: st.session_state.current_page = "Dashboard"
if 'selected_zone' not in st.session_state: st.session_state.selected_zone = "Zone 1"
if 'watering_mode' not in st.session_state: st.session_state.watering_mode = "Auto"
if 'zone_configs' not in st.session_state:
    st.session_state.zone_configs = {f"Zone {i}": {"crop": "Large Cardamom", "target_moisture": 55} for i in range(1, 5)}
if 'daily_water' not in st.session_state or st.session_state.daily_water.get('date') != date.today():
    st.session_state.daily_water = {"date": date.today(), **{f"Zone {i}": 0 for i in range(1, 5)}}

# --- 3. DETAILED CROP KNOWLEDGE BASE (WITH CORRECTED IMAGE URLS) ---
CROP_KNOWLEDGE = {
    'Large Cardamom': {
        'daily_water_limit_L': 20, 'temp_range': (18, 28), 'humidity_range': (70, 85),
        'soil_type': 'Well-drained, rich in organic matter',
        'description': "A spice with a strong, aromatic flavor thriving in humid, subtropical climates with partial shade.",
        'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394"
    },
    'Ginger': {
        'daily_water_limit_L': 15, 'temp_range': (20, 30), 'humidity_range': (60, 75),
        'soil_type': 'Rich, loamy, well-drained soil',
        'description': "A flowering plant whose rhizome is widely used as a spice. It prefers warm, humid climates with rich, moist soil.",
        'image_url': "https://upload.wikimedia.org/wikipedia/commons/a/a7/Ginger_root.jpg" # Corrected URL
    },
    'Mandarin Orange': {
        'daily_water_limit_L': 25, 'temp_range': (22, 32), 'humidity_range': (50, 70),
        'soil_type': 'Well-drained, slightly acidic soil',
        'description': "Small, sweet citrus fruits that grow best in warm, sunny climates and require consistent watering during fruit development.",
        'image_url': "https://upload.wikimedia.org/wikipedia/commons/thumb/1/14/Mandarins_tangerines.jpg/1280px-Mandarins_tangerines.jpg" # Corrected URL
    }
}

# --- 4. SIDEBAR WITH AUTOSAVE ---
def update_config(zone_key):
    config = st.session_state.zone_configs[zone_key]
    config['crop'] = st.session_state[f"crop_{zone_key}"]
    config['target_moisture'] = st.session_state[f"moisture_{zone_key}"]

with st.sidebar:
    st.header("⚙️ Zone Configuration")
    st.caption("Changes are saved automatically.")
    for zone in sorted(st.session_state.zone_configs.keys()):
        st.markdown(f"#### {zone}")
        cfg = st.session_state.zone_configs[zone]
        st.selectbox("Assign Crop", CROP_KNOWLEDGE.keys(), list(CROP_KNOWLEDGE.keys()).index(cfg["crop"]), key=f"crop_{zone}", on_change=update_config, args=(zone,))
        st.slider("Target Soil Moisture (%)", 0, 100, cfg["target_moisture"], key=f"moisture_{zone}", on_change=update_config, args=(zone,))
        st.markdown("---")

# --- 5. UI PAGES ---
def dashboard_page():
    st.session_state.selected_zone = st.radio("Select Zone", [f"Zone {i}" for i in range(1, 5)], horizontal=True)
    st.markdown("---")
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
    
    # --- ERROR FIX: Only show watering control if live data is available ---
    if zone_data:
        with col2:
            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.subheader("💧 Watering Control")
            limit = crop_info['daily_water_limit_L']; given = st.session_state.daily_water[st.session_state.selected_zone]
            remaining = max(0, limit - given)
            st.progress(given / limit if limit else 0, text=f"{given:.1f} / {limit} L used today")
            
            if remaining <= 0:
                st.success("✅ Daily water limit reached.")
            else:
                btn_cols = st.columns(2)
                if btn_cols[0].button("Auto", use_container_width=True, type="primary" if st.session_state.watering_mode == "Auto" else "secondary"): st.session_state.watering_mode = "Auto"
                if btn_cols[1].button("Manual", use_container_width=True, type="primary" if st.session_state.watering_mode == "Manual" else "secondary"): st.session_state.watering_mode = "Manual"

                amount = 0
                if st.session_state.watering_mode == "Manual":
                    amount = st.number_input("Amount (L)", 0.0, remaining, min(1.0, remaining), 0.5)
                else:
                    target = zone_config['target_moisture']
                    current = zone_data.get('soil_moisture', target)
                    auto_amount = round(max(0, target - current) * 0.5, 1)
                    amount = min(auto_amount, remaining)
                    st.info(f"Auto-Calculated: {amount} L")

                if st.button("💦 Water Now", use_container_width=True, disabled=(amount<=0)):
                    st.session_state.daily_water[st.session_state.selected_zone] += amount
                    st.success(f"Watered with {amount} L."); time.sleep(1); st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

def crops_page():
    st.header("📚 Crop Knowledge Base")
    selected_crop = st.selectbox("Select a crop to view its profile", CROP_KNOWLEDGE.keys())
    if selected_crop:
        info = CROP_KNOWLEDGE[selected_crop]
        st.markdown('<div class="card">', unsafe_allow_html=True)
        c1, c2 = st.columns([1, 2])
        if info.get('image_url'): c1.image(info['image_url'], caption=selected_crop)
        with c2:
            st.subheader(f"Profile: {selected_crop}")
            st.metric("Daily Water Limit", f"{info['daily_water_limit_L']} Liters/day")
            m_cols = st.columns(2)
            m_cols[0].metric("Ideal Temperature", f"{info['temp_range'][0]} - {info['temp_range'][1]} °C")
            m_cols[1].metric("Ideal Humidity", f"{info['humidity_range'][0]} - {info['humidity_range'][1]} %")
            st.write(f"**Preferred Soil:** {info['soil_type']}")
            st.write(f"**Description:** {info['description']}")
        st.markdown('</div>', unsafe_allow_html=True)

def profile_page():
    st.header("👤 Farmer Profile")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.write("### Rajesh Kumar")
    st.write("📍 Sikkim, India")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. NAVIGATION & PAGE ROUTER ---
title_col, nav_col = st.columns([2, 3])
with title_col: st.markdown('<h1 class="main-header">🌿 AgroSmart</h1>', unsafe_allow_html=True)
with nav_col:
    st.write(""); st.write("") # Vertical spacer
    pages = ["Dashboard", "Crops", "Profile"]
    icons = ["🏠", "🌱", "👤"]
    nav_cols = st.columns(3)
    for i, page in enumerate(pages):
        if nav_cols[i].button(f"{icons[i]} {page}", use_container_width=True):
            st.session_state.current_page = page; st.rerun()

st.markdown("---")

# Router logic
if st.session_state.current_page == "Dashboard": dashboard_page()
elif st.session_state.current_page == "Crops": crops_page()
elif st.session_state.current_page == "Profile": profile_page()
