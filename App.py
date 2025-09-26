import streamlit as st
import requests

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="🌿 AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide"
)

BACKEND_URL = "https://agrosmart-flask-backend.onrender.com"

# --- CSS STYLING ---
st.markdown("""
<style>
.stApp {
    background: linear-gradient(to right, #eafaf3, #ffffff);
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}
.zone-card {
    background: white;
    border-radius: 15px;
    padding: 20px;
    margin-bottom: 15px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}
.zone-card:hover {
    transform: translateY(-5px);
}
.circular-progress {
    width: 100px;
    height: 100px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
    position: relative;
    background: conic-gradient(#4caf50 0%, #e0e0e0 0%);
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
}
.circular-progress::before {
    content: "";
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: white;
    position: absolute;
}
.progress-value {
    position: relative;
    font-size: 1.2rem;
    font-weight: bold;
    color: #2e7d32;
}
.progress-label {
    text-align: center;
    margin-top: 5px;
    font-weight: bold;
    color: #555;
}
.water-alert {
    background: #fff3e0;
    border-left: 4px solid #ff9800;
    color: #e65100;
    padding: 10px;
    border-radius: 8px;
    margin-top: 10px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- SESSION STATE ---
if 'zone_data' not in st.session_state:
    st.session_state.zone_data = {
        f"Zone {i}": {
            'crop': 'Large Cardamom',
            'target_moisture': 55,
            'soil_moisture': 0,
            'temperature': 0,
            'humidity': 0,
        } for i in range(1, 5)
    }

# --- CROP KNOWLEDGE ---
CROP_KNOWLEDGE = {
    'Large Cardamom': {
        'temp_range': (18, 28),
        'humidity_range': (70, 85),
        'description': "Large cardamom is a spice with a strong, aromatic, and smoky flavor. Thrives in humid, subtropical climates with well-drained soil and partial shade. Used in Indian and Nepalese cuisine.",
        'water_needs': "Moderate to high, consistently moist soil.",
        'soil_type': "Well-drained, rich in organic matter.",
        'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394&width=1445"
    },
    'Ginger': {
        'temp_range': (20, 30),
        'humidity_range': (60, 75),
        'description': "Ginger is a flowering plant whose rhizome is widely used as a spice and folk medicine. Prefers warm, humid climates with rich, moist soil.",
        'water_needs': "Regular watering, avoid waterlogging.",
        'soil_type': "Rich, loamy, well-drained soil.",
        'image_url': "https://organicmandya.com/cdn/shop/files/Ginger.jpg?v=1757079802&width=1000"
    },
    'Mandarin Orange': {
        'temp_range': (22, 32),
        'humidity_range': (50, 70),
        'description': "Mandarin oranges are small, sweet citrus fruits. Grow best in warm, sunny climates with well-drained soil. Requires consistent watering during fruit development.",
        'water_needs': "Regular watering during fruiting.",
        'soil_type': "Well-drained, slightly acidic soil.",
        'image_url': "https://www.stylecraze.com/wp-content/uploads/2013/11/845_14-Amazing-Benefits-Of-Mandarin-Oranges-For-Skin-Hair-And-Health_shutterstock_116644108_1200px.jpg.webp"
    },
}

CROP_OPTIONS = list(CROP_KNOWLEDGE.keys())

# --- FETCH DATA FROM BACKEND ---
def fetch_data():
    try:
        res = requests.get(f"{BACKEND_URL}/zones", timeout=5)
        res.raise_for_status()
        data = res.json()
        for zone_name, values in data.items():
            st.session_state.zone_data[zone_name]['soil_moisture'] = values.get('soil_moisture', 0)
            st.session_state.zone_data[zone_name]['temperature'] = values.get('temperature', 0)
            st.session_state.zone_data[zone_name]['humidity'] = values.get('humidity', 0)
        return True
    except:
        st.warning("⚠ Could not fetch live sensor data.")
        return False

# --- HEADER ---
st.title("🌿 AgroSmart Live Dashboard")
st.markdown("Monitor and control your farm's irrigation zones in real-time.")

# --- SIDEBAR: CROP ASSIGNMENT & TARGETS ---
with st.sidebar:
    st.header("⚙️ Farm Settings")
    st.subheader("Assign Crop to Each Zone")
    for zone_name in st.session_state.zone_data:
        st.session_state.zone_data[zone_name]['crop'] = st.selectbox(
            f"{zone_name} Crop", CROP_OPTIONS, 
            index=CROP_OPTIONS.index(st.session_state.zone_data[zone_name]['crop']),
            key=f"crop_{zone_name}"
        )
    st.markdown("---")
    st.subheader("Set Target Soil Moisture")
    for zone_name in st.session_state.zone_data:
        st.session_state.zone_data[zone_name]['target_moisture'] = st.slider(
            f"{zone_name} Target Moisture", 0, 100,
            st.session_state.zone_data[zone_name]['target_moisture'], key=f"target_{zone_name}"
        )
    st.markdown("---")
    if st.button("🔄 Refresh Sensor Data", use_container_width=True):
        fetch_data()

# --- MAIN DASHBOARD ---
st.header("Irrigation Zone Overview")

cols = st.columns(4)
for i, zone_name in enumerate(st.session_state.zone_data):
    data = st.session_state.zone_data[zone_name]
    with cols[i]:
        st.markdown(f"<div class='zone-card'>", unsafe_allow_html=True)
        st.subheader(zone_name)
        st.markdown(f"**Crop:** {data['crop']}")
        st.markdown(f"**Target Moisture:** {data['target_moisture']}%")

        # Circular progress bars
        st.markdown(f"""
        <div class="circular-progress" style="background: conic-gradient(#ff9800 {min(100, data['temperature'])}%, #e0e0e0 0%);">
            <div class="progress-value">{data['temperature']}°C</div>
        </div>
        <div class="progress-label">Temperature</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="circular-progress" style="background: conic-gradient(#2196f3 {min(100, data['humidity'])}%, #e0e0e0 0%);">
            <div class="progress-value">{data['humidity']}%</div>
        </div>
        <div class="progress-label">Humidity</div>
        """, unsafe_allow_html=True)

        st.markdown(f"""
        <div class="circular-progress" style="background: conic-gradient(#4caf50 {min(100, data['soil_moisture'])}%, #e0e0e0 0%);">
            <div class="progress-value">{data['soil_moisture']}%</div>
        </div>
        <div class="progress-label">Soil Moisture</div>
        """, unsafe_allow_html=True)

        if data['soil_moisture'] < data['target_moisture']:
            st.markdown("<div class='water-alert'>⚠ Water Needed!</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

# --- CROP KNOWLEDGE BASE ---
st.markdown("---")
st.header("📚 Crop Knowledge Base")
selected_crop = st.selectbox("Select a crop to learn more:", CROP_OPTIONS, index=0
