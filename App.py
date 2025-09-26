import streamlit as st
import requests
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import time
import os

# Page configuration
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FINAL BACKEND URL ---
# Updated with the link you provided.
BACKEND_URL = "https://agrosmart-flask-backend.onrender.com"

# --- CROP INFORMATION ---
CROP_INFO = {
    "Tomato": { "image_url": "https://images.unsplash.com/photo-1546470427-5c8b0b0b0b0b?w=300", "temp_range": [18, 25], "humidity_range": [60, 80], "description": "Tomatoes require consistent moisture and warm temperatures." },
    "Lettuce": { "image_url": "https://images.unsplash.com/photo-1556801712-76c8eb07bbc9?w=300", "temp_range": [15, 20], "humidity_range": [70, 85], "description": "Lettuce prefers cool temperatures and high humidity." },
    "Pepper": { "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300", "temp_range": [20, 30], "humidity_range": [50, 70], "description": "Peppers thrive in warm conditions with moderate humidity." },
    "Cucumber": { "image_url": "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=300", "temp_range": [18, 24], "humidity_range": [60, 75], "description": "Cucumbers need consistent moisture and moderate temperatures." }
}

# --- API HELPER FUNCTIONS ---
def fetch_data_from_backend():
    """Fetch latest data for all zones from the backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/data", timeout=15)
        response.raise_for_status() # Raises an exception for 4xx/5xx errors
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to backend: {e}")
        return None

def fetch_zone_history(zone_id):
    """Fetch historical data for a specific zone"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/data/{zone_id}", timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch history for Zone {zone_id}: {e}")
        return None

def manual_pump_control(zone_id, action):
    """Send manual pump control command to the backend"""
    try:
        response = requests.post(f"{BACKEND_URL}/api/pump/{zone_id}", json={"action": action}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send pump command: {e}")
        return None

# --- SIDEBAR ---
st.sidebar.header("Crop Information")
selected_crop = st.sidebar.selectbox("Select Crop Type", list(CROP_INFO.keys()))

if selected_crop:
    info = CROP_INFO[selected_crop]
    st.sidebar.image(info['image_url'], caption=selected_crop, use_container_width=True)
    st.sidebar.write(f"**Ideal Temp:** {info['temp_range'][0]}°C - {info['temp_range'][1]}°C")
    st.sidebar.write(f"**Ideal Humidity:** {info['humidity_range'][0]}% - {info['humidity_range'][1]}%")
    st.sidebar.info(info['description'])

st.sidebar.markdown("---")
# Manual refresh button is more reliable than auto-refresh with st.rerun()
if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    st.experimental_rerun()


# --- MAIN DASHBOARD ---
st.title("🌱 AgroSmart Farm Monitoring Dashboard")

# Fetch and display data
data = fetch_data_from_backend()

if data:
    # Create columns for each zone
    cols = st.columns(4)
    
    for i, (zone_key, zone_data) in enumerate(data.items()):
        with cols[i]:
            zone_id = zone_data['zone_id']
            st.subheader(f"Zone {zone_id}")
            
            # Display sensor readings
            st.metric("🌡 Temperature", f"{zone_data['temperature']:.1f}°C")
            st.metric("💧 Soil Moisture", f"{zone_data['soil_moisture']:.1f}%")
            st.metric("💨 Humidity", f"{zone_data['humidity']:.1f}%")
            rain_status = "🌧 Raining" if zone_data['is_raining'] else "☀️ Clear"
            st.metric("Weather", rain_status)
            
            # Pump status and control
            st.write("---")
            st.write("**Pump Control**")
            
            col_on, col_off = st.columns(2)
            if col_on.button("ON", key=f"pump_on_{zone_id}", use_container_width=True):
                if manual_pump_control(zone_id, "on"):
                    st.success("Pump turned ON")
                    time.sleep(1) # Brief pause to show message
                    st.experimental_rerun()
            
            if col_off.button("OFF", key=f"pump_off_{zone_id}", use_container_width=True):
                if manual_pump_control(zone_id, "off"):
                    st.success("Pump turned OFF")
                    time.sleep(1)
                    st.experimental_rerun()
            
            last_update = datetime.fromisoformat(zone_data['timestamp'])
            st.caption(f"Last update: {last_update.strftime('%H:%M:%S')}")

    # --- Historical data charts ---
    st.markdown("---")
    st.header("📊 Historical Data")
    
    selected_zone_for_history = st.selectbox("Select Zone for Detailed View", [1, 2, 3, 4])
    
    if st.button("📈 Load Historical Data", key="load_history"):
        with st.spinner(f"Loading data for Zone {selected_zone_for_history}..."):
            history_data = fetch_zone_history(selected_zone_for_history)
            
            if history_data:
                df = pd.DataFrame(history_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Create charts
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['temperature'], mode='lines+markers', name='Temperature (°C)', line=dict(color='red')))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['humidity'], mode='lines+markers', name='Humidity (%)', line=dict(color='blue'), yaxis='y2'))
                fig.add_trace(go.Scatter(x=df['timestamp'], y=df['soil_moisture'], mode='lines+markers', name='Soil Moisture (%)', line=dict(color='green'), yaxis='y3'))
                
                fig.update_layout(
                    title=f'Zone {selected_zone_for_history} - Sensor Readings (Last 24h)',
                    xaxis_title='Time',
                    yaxis=dict(title='Temperature (°C)', side='left'),
                    yaxis2=dict(title='Humidity (%)', side='right', overlaying='y'),
                    yaxis3=dict(title='Soil Moisture (%)', side='right', overlaying='y', position=0.95),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Raw Data")
                st.dataframe(df[['timestamp', 'temperature', 'humidity', 'soil_moisture', 'is_raining', 'pump_activated']])
            else:
                st.error("No historical data available for this zone.")

else:
    st.error("❌ Failed to load data from backend.")
    st.info("Please wait a moment for the backend to start, or check the URL and your connection.")

# --- Footer ---
st.markdown("---")
st.markdown("*AgroSmart Farm Monitoring System*")

