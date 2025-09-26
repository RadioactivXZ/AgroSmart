import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Page configuration
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌱",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Backend URL - Update this with your deployed backend URL
BACKEND_URL = "https://agrosmartback.onrender.com"  # Update this URL

# Crop information database
CROP_INFO = {
    "Tomato": {
        "image_url": "https://images.unsplash.com/photo-1546470427-5c8b0b0b0b0b?w=300",
        "temp_range": [18, 25],
        "humidity_range": [60, 80],
        "description": "Tomatoes require consistent moisture and warm temperatures for optimal growth."
    },
    "Lettuce": {
        "image_url": "https://images.unsplash.com/photo-1556801712-76c8eb07bbc9?w=300",
        "temp_range": [15, 20],
        "humidity_range": [70, 85],
        "description": "Lettuce prefers cool temperatures and high humidity for crisp, tender leaves."
    },
    "Pepper": {
        "image_url": "https://images.unsplash.com/photo-1518977676601-b53f82aba655?w=300",
        "temp_range": [20, 30],
        "humidity_range": [50, 70],
        "description": "Peppers thrive in warm conditions with moderate humidity levels."
    },
    "Cucumber": {
        "image_url": "https://images.unsplash.com/photo-1449300079323-02e209d9d3a6?w=300",
        "temp_range": [18, 24],
        "humidity_range": [60, 75],
        "description": "Cucumbers need consistent moisture and moderate temperatures for best yield."
    }
}

def fetch_data_from_backend():
    """Fetch data from the backend API"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/data", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Backend returned status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to connect to backend: {str(e)}")
        return None

def fetch_zone_history(zone_id, hours=24):
    """Fetch historical data for a specific zone"""
    try:
        response = requests.get(f"{BACKEND_URL}/api/data/{zone_id}", timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to fetch zone {zone_id} data: {str(e)}")
        return None

def manual_pump_control(zone_id, action):
    """Send manual pump control command"""
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/pump/{zone_id}",
            json={"action": action},
            timeout=10
        )
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Failed to control pump: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        st.error(f"Failed to send pump command: {str(e)}")
        return None

# Main Dashboard
st.title("🌱 AgroSmart Farm Monitoring Dashboard")

# Sidebar for crop selection
st.sidebar.header("Crop Information")
selected_crop = st.sidebar.selectbox("Select Crop Type", list(CROP_INFO.keys()))

# Display crop information
if selected_crop:
    info = CROP_INFO[selected_crop]
    col_img, col_text = st.sidebar.columns([1, 2])
    
    with col_img:
        st.image(info['image_url'], caption=selected_crop, use_container_width=True)
    
    with col_text:
        st.write(f"Ideal Temperature Range: {info['temp_range'][0]}°C - {info['temp_range'][1]}°C")
        st.write(f"Ideal Humidity Range: {info['humidity_range'][0]}% - {info['humidity_range'][1]}%")
        st.write("---")
        st.markdown(f"Description: {info['description']}")

# Auto-refresh toggle
auto_refresh = st.sidebar.checkbox("Auto-refresh (30s)", value=True)
if auto_refresh:
    time.sleep(30)
    st.rerun()

# Manual refresh button
if st.sidebar.button("🔄 Refresh Data"):
    st.rerun()

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
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "🌡 Temperature", 
                    f"{zone_data['temperature']:.1f}°C",
                    delta=None
                )
                st.metric(
                    "💧 Soil Moisture", 
                    f"{zone_data['soil_moisture']:.1f}%",
                    delta=None
                )
            
            with col2:
                st.metric(
                    "   Humidity", 
                    f"{zone_data['humidity']:.1f}%",
                    delta=None
                )
                rain_status = "🌧 Raining" if zone_data['is_raining'] else "☀ Clear"
                st.metric("Weather", rain_status)
            
            # Pump status and control
            st.write("---")
            st.write("*Pump Control*")
            
            # Manual pump controls
            col_on, col_off = st.columns(2)
            with col_on:
                if st.button(f"   ON", key=f"pump_on_{zone_id}"):
                    result = manual_pump_control(zone_id, "on")
                    if result:
                        st.success("Pump turned ON")
                        st.rerun()
            
            with col_off:
                if st.button(f"⏹ OFF", key=f"pump_off_{zone_id}"):
                    result = manual_pump_control(zone_id, "off")
                    if result:
                        st.success("Pump turned OFF")
                        st.rerun()
            
            # Show last update time
            last_update = datetime.fromisoformat(zone_data['timestamp'].replace('Z', '+00:00'))
            st.caption(f"Last update: {last_update.strftime('%H:%M:%S')}")
    
    # Historical data charts
    st.header("📊 Historical Data")
    
    # Zone selection for detailed view
    selected_zone = st.selectbox("Select Zone for Detailed View", [1, 2, 3, 4])
    
    if st.button("📈 Load Historical Data"):
        with st.spinner(f"Loading data for Zone {selected_zone}..."):
            history_data = fetch_zone_history(selected_zone)
            
            if history_data:
                # Convert to DataFrame
                df = pd.DataFrame(history_data)
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                
                # Create charts
                fig = go.Figure()
                
                # Temperature
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['temperature'],
                    mode='lines+markers',
                    name='Temperature (°C)',
                    line=dict(color='red')
                ))
                
                # Humidity
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['humidity'],
                    mode='lines+markers',
                    name='Humidity (%)',
                    line=dict(color='blue'),
                    yaxis='y2'
                ))
                
                # Soil Moisture
                fig.add_trace(go.Scatter(
                    x=df['timestamp'],
                    y=df['soil_moisture'],
                    mode='lines+markers',
                    name='Soil Moisture (%)',
                    line=dict(color='green'),
                    yaxis='y3'
                ))
                
                # Update layout
                fig.update_layout(
                    title=f'Zone {selected_zone} - Sensor Readings Over Time',
                    xaxis_title='Time',
                    yaxis=dict(title='Temperature (°C)', side='left'),
                    yaxis2=dict(title='Humidity (%)', side='right', overlaying='y'),
                    yaxis3=dict(title='Soil Moisture (%)', side='right', overlaying='y', position=0.95),
                    hovermode='x unified'
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Data table
                st.subheader("Raw Data")
                st.dataframe(df[['timestamp', 'temperature', 'humidity', 'soil_moisture', 'is_raining', 'pump_activated']])
            else:
                st.error("No historical data available for this zone")

else:
    st.error("❌ Failed to load data from backend. Please check your connection.")
    st.info("Make sure your backend is running and accessible.")

# Footer
st.markdown("---")
st.markdown("*AgroSmart Farm Monitoring System* | Built with Streamlit & Flask")
