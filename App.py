import streamlit as st
import requests
import time
import random

# --- 1. CONFIGURATION ---
st.set_page_config(
    page_title="AgroSmart Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# URL of your hosted backend API
BACKEND_URL = "https://agrosmartback.onrender.com/"

# --- Custom CSS for Aesthetic Styling ---
st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(to bottom right, #f0f8f0, #e0f0e0);
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    
    /* Header styling */
    .header-container {
        background: linear-gradient(to right, #2e7d32, #4caf50);
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: white;
    }
    
    /* Zone selector styling */
    .zone-selector {
        display: flex;
        justify-content: space-between;
        margin-bottom: 2rem;
    }
    
    .zone-button {
        flex: 1;
        margin: 0 5px;
        padding: 15px 10px;
        border-radius: 15px;
        background: linear-gradient(to bottom, #ffffff, #f5f5f5);
        border: 2px solid #4caf50;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        font-weight: bold;
        color: #2e7d32;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    
    .zone-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        background: linear-gradient(to bottom, #e8f5e9, #c8e6c9);
    }
    
    .zone-button.active {
        background: linear-gradient(to bottom, #4caf50, #2e7d32);
        color: white;
        border-color: #1b5e20;
    }
    
    /* Circular progress bars */
    .circular-progress {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        margin: 0 auto;
        position: relative;
        background: conic-gradient(#4caf50 0%, #e0e0e0 0%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    .circular-progress::before {
        content: "";
        width: 100px;
        height: 100px;
        border-radius: 50%;
        background: white;
        position: absolute;
    }
    
    .progress-value {
        position: relative;
        font-size: 1.5rem;
        font-weight: bold;
        color: #2e7d32;
    }
    
    .progress-label {
        text-align: center;
        margin-top: 10px;
        font-weight: bold;
        color: #555;
    }
    
    /* Water control panel */
    .water-control {
        background: white;
        border-radius: 15px;
        padding: 20px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
        margin: 20px 0;
        border-left: 5px solid #4caf50;
    }
    
    /* Crop info cards */
    .crop-card {
        background: white;
        border-radius: 10px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border-left: 4px solid #4caf50;
    }
    
    /* Notification styling */
    .notification {
        padding: 10px 15px;
        border-radius: 8px;
        margin: 10px 0;
        font-weight: bold;
    }
    
    .notification.warning {
        background: #fff3e0;
        border-left: 4px solid #ff9800;
        color: #e65100;
    }
    
    .notification.success {
        background: #e8f5e9;
        border-left: 4px solid #4caf50;
        color: #2e7d32;
    }
    
    .notification.info {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
        color: #0d47a1;
    }
    
    /* Login form styling */
    .login-container {
        max-width: 400px;
        margin: 100px auto;
        padding: 30px;
        background: white;
        border-radius: 15px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.1);
    }
    </style>
    """,
    unsafe_allow_html=True
)

# --- 2. SESSION STATE & DATA ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False

if 'current_zone' not in st.session_state:
    st.session_state.current_zone = "Zone 1"

if 'zone_data' not in st.session_state:
    # Initialize with sample data
    st.session_state.zone_data = {
        "Zone 1": {
            'crop': 'Large Cardamom',
            'target_moisture': 55,
            'soil_moisture': 42,
            'temperature': 24.5,
            'humidity': 72,
            'water_needed': True,
            'status': 'Needs Attention',
            'manual_water_level': 30
        },
        "Zone 2": {
            'crop': 'Ginger',
            'target_moisture': 60,
            'soil_moisture': 58,
            'temperature': 26.2,
            'humidity': 68,
            'water_needed': False,
            'status': 'Optimal',
            'manual_water_level': 0
        },
        "Zone 3": {
            'crop': 'Mandarin Orange',
            'target_moisture': 50,
            'soil_moisture': 35,
            'temperature': 28.7,
            'humidity': 55,
            'water_needed': True,
            'status': 'Needs Water',
            'manual_water_level': 0
        },
        "Zone 4": {
            'crop': 'Large Cardamom',
            'target_moisture': 55,
            'soil_moisture': 62,
            'temperature': 23.8,
            'humidity': 78,
            'water_needed': False,
            'status': 'Optimal',
            'manual_water_level': 0
        }
    }

# Crop knowledge base
CROP_KNOWLEDGE = {
    'Large Cardamom': {
        'temp_range': (18, 28),
        'humidity_range': (70, 85),
        'water_needs': 'Moderate to high, prefers consistently moist soil',
        'soil_type': 'Well-drained, rich in organic matter',
        'description': "Large cardamom is a spice with a strong, aromatic, and smoky flavor. It thrives in humid, subtropical climates with well-drained soil and partial shade. It's often used in Indian and Nepalese cuisine.",
        'image_url': "https://masalaboxco.com/cdn/shop/files/2_62858b80-ebe4-431e-9454-b103a07bb5ae.png?v=1702990394&width=1445"
    },
    'Ginger': {
        'temp_range': (20, 30),
        'humidity_range': (60, 75),
        'water_needs': 'Regular watering, but avoid waterlogging',
        'soil_type': 'Rich, loamy, well-drained soil',
        'description': "Ginger is a flowering plant whose rhizome (underground stem) is widely used as a spice and folk medicine. It prefers warm, humid climates with rich, moist soil. It's a versatile crop used in cooking, beverages, and traditional remedies.",
        'image_url': "https://organicmandya.com/cdn/shop/files/Ginger.jpg?v=1757079802&width=1000"
    },
    'Mandarin Orange': {
        'temp_range': (22, 32),
        'humidity_range': (50, 70),
        'water_needs': 'Regular watering, especially during fruit development',
        'soil_type': 'Well-drained, slightly acidic soil',
        'description': "Mandarin oranges are small, sweet citrus fruits. They grow best in warm, sunny climates with well-drained soil. They are less cold-tolerant than other citrus and require consistent watering during fruit development.",
        'image_url': "https://www.stylecraze.com/wp-content/uploads/2013/11/845_14-Amazing-Benefits-Of-Mandarin-Oranges-For-Skin-Hair-And-Health_shutterstock_116644108_1200px.jpg.webp"
    },
}

# --- 3. LOGIN PAGE ---
def login_page():
    st.markdown(
        """
        <div class="login-container">
            <h2 style="text-align: center; color: #2e7d32;">🌿 AgroSmart Login</h2>
            <p style="text-align: center; color: #666;">Access your farm dashboard</p>
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    with st.form("login_form"):
        phone = st.text_input("Phone Number", placeholder="Enter your phone number")
        password = st.text_input("Password", type="password", placeholder="Enter your password")
        submit = st.form_submit_button("Login", use_container_width=True)
        
        if submit:
            if phone and password:
                # Simple authentication (in real app, verify against database)
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("Please enter both phone number and password")

# --- 4. MAIN DASHBOARD ---
def main_dashboard():
    # Header with navigation
    col1, col2, col3, col4, col5 = st.columns([2,1,1,1,1])
    
    with col1:
        st.markdown("<h1 style='color: #2e7d32; margin-bottom: 0;'>🌿 AgroSmart</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color: #666; margin-top: 0;'>Smart Irrigation System</p>", unsafe_allow_html=True)
    
    with col2:
        if st.button("🏠 Home", use_container_width=True):
            st.session_state.current_page = "home"
    
    with col3:
        if st.button("🌱 Crops", use_container_width=True):
            st.session_state.current_page = "crops"
    
    with col4:
        if st.button("🔔 Notifications", use_container_width=True):
            st.session_state.current_page = "notifications"
    
    with col5:
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.current_page = "profile"
    
    st.markdown("---")
    
    # Page routing
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "home"
    
    if st.session_state.current_page == "home":
        home_page()
    elif st.session_state.current_page == "crops":
        crops_page()
    elif st.session_state.current_page == "notifications":
        notifications_page()
    elif st.session_state.current_page == "profile":
        profile_page()

# --- 5. HOME PAGE ---
def home_page():
    # Zone selector
    st.markdown("<h2>Irrigation Zones</h2>", unsafe_allow_html=True)
    
    # Create zone buttons
    cols = st.columns(4)
    for i, col in enumerate(cols):
        zone_name = f"Zone {i+1}"
        zone_data = st.session_state.zone_data[zone_name]
        
        # Determine button style based on status
        button_class = "active" if zone_name == st.session_state.current_zone else ""
        status_color = "#ff9800" if zone_data['water_needed'] else "#4caf50"
        
        with col:
            st.markdown(
                f"""
                <div class="zone-button {button_class}" onclick="setZone('{zone_name}')">
                    <div style="font-size: 1.2rem;">{zone_name}</div>
                    <div style="font-size: 0.9rem; color: {status_color};">{zone_data['status']}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    st.markdown("---")
    
    # Current zone display
    zone_data = st.session_state.zone_data[st.session_state.current_zone]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Sensor data display with circular progress bars
        st.markdown(f"<h3>{st.session_state.current_zone} - {zone_data['crop']}</h3>", unsafe_allow_html=True)
        
        # Create three columns for circular progress bars
        prog_col1, prog_col2, prog_col3 = st.columns(3)
        
        with prog_col1:
            # Temperature progress (scaled to show 0-40°C range)
            temp_percent = min(100, (zone_data['temperature'] / 40) * 100)
            st.markdown(
                f"""
                <div class="circular-progress" style="background: conic-gradient(#ff9800 {temp_percent}%, #e0e0e0 0%);">
                    <div class="progress-value">{zone_data['temperature']}°C</div>
                </div>
                <div class="progress-label">Temperature</div>
                """, 
                unsafe_allow_html=True
            )
        
        with prog_col2:
            # Humidity progress
            st.markdown(
                f"""
                <div class="circular-progress" style="background: conic-gradient(#2196f3 {zone_data['humidity']}%, #e0e0e0 0%);">
                    <div class="progress-value">{zone_data['humidity']}%</div>
                </div>
                <div class="progress-label">Humidity</div>
                """, 
                unsafe_allow_html=True
            )
        
        with prog_col3:
            # Soil moisture progress
            st.markdown(
                f"""
                <div class="circular-progress" style="background: conic-gradient(#4caf50 {zone_data['soil_moisture']}%, #e0e0e0 0%);">
                    <div class="progress-value">{zone_data['soil_moisture']}%</div>
                </div>
                <div class="progress-label">Soil Moisture</div>
                """, 
                unsafe_allow_html=True
            )
        
        # Water needed message
        if zone_data['water_needed']:
            st.markdown(
                f"""
                <div class="water-control">
                    <h3 style="color: #e65100;">⚠️ Water Needed</h3>
                    <p>Current moisture: {zone_data['soil_moisture']}% | Target: {zone_data['target_moisture']}%</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"""
                <div class="water-control">
                    <h3 style="color: #2e7d32;">✅ Optimal Conditions</h3>
                    <p>Current moisture: {zone_data['soil_moisture']}% | Target: {zone_data['target_moisture']}%</p>
                </div>
                """, 
                unsafe_allow_html=True
            )
    
    with col2:
        # Water control panel
        st.markdown("<h3>Water Control</h3>", unsafe_allow_html=True)
        
        # Automatic watering option
        auto_water = st.checkbox("Automatic Watering", value=not zone_data['water_needed'])
        
        if not auto_water:
            # Manual water control
            water_amount = st.slider("Water Amount (Liters)", 0, 100, zone_data['manual_water_level'])
            st.session_state.zone_data[st.session_state.current_zone]['manual_water_level'] = water_amount
            
            # Manual input for precise control
            manual_input = st.number_input("Or enter exact amount", 0, 100, water_amount)
            if manual_input != water_amount:
                st.session_state.zone_data[st.session_state.current_zone]['manual_water_level'] = manual_input
                st.rerun()
        
        # Water button
        if st.button("💧 Water Now", use_container_width=True, type="primary"):
            if auto_water:
                # Calculate needed water based on deficit
                deficit = max(0, zone_data['target_moisture'] - zone_data['soil_moisture'])
                water_amount = min(100, deficit * 2)  # Simple formula
                st.success(f"Automatically watering with {water_amount}L")
            else:
                water_amount = zone_data['manual_water_level']
                st.success(f"Manually watering with {water_amount}L")
            
            # Simulate watering effect
            st.session_state.zone_data[st.session_state.current_zone]['soil_moisture'] = min(
                100, zone_data['soil_moisture'] + (water_amount / 4)
            )
            st.session_state.zone_data[st.session_state.current_zone]['water_needed'] = False
            st.session_state.zone_data[st.session_state.current_zone]['status'] = 'Optimal'
            st.rerun()
    
    # Crop details
    st.markdown("---")
    st.markdown("<h3>Crop Details</h3>", unsafe_allow_html=True)
    
    crop_info = CROP_KNOWLEDGE[zone_data['crop']]
    info_col1, info_col2 = st.columns([1, 2])
    
    with info_col1:
        st.image(crop_info['image_url'], use_container_width=True)
    
    with info_col2:
        st.markdown(f"**Ideal Temperature:** {crop_info['temp_range'][0]}°C - {crop_info['temp_range'][1]}°C")
        st.markdown(f"**Ideal Humidity:** {crop_info['humidity_range'][0]}% - {crop_info['humidity_range'][1]}%")
        st.markdown(f"**Water Needs:** {crop_info['water_needs']}")
        st.markdown(f"**Soil Type:** {crop_info['soil_type']}")
        st.markdown(f"**Description:** {crop_info['description']}")

# --- 6. CROPS PAGE ---
def crops_page():
    st.markdown("<h2>Crop Information</h2>", unsafe_allow_html=True)
    
    selected_crop = st.selectbox(
        "Select a crop to learn more:",
        options=list(CROP_KNOWLEDGE.keys()),
        index=0
    )
    
    if selected_crop:
        crop_info = CROP_KNOWLEDGE[selected_crop]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.image(crop_info['image_url'], use_container_width=True)
        
        with col2:
            st.markdown(f"## {selected_crop}")
            st.markdown(f"**Ideal Temperature Range:** {crop_info['temp_range'][0]}°C - {crop_info['temp_range'][1]}°C")
            st.markdown(f"**Ideal Humidity Range:** {crop_info['humidity_range'][0]}% - {crop_info['humidity_range'][1]}%")
            st.markdown(f"**Water Needs:** {crop_info['water_needs']}")
            st.markdown(f"**Soil Type:** {crop_info['soil_type']}")
            st.markdown("---")
            st.markdown(f"**Description:** {crop_info['description']}")
            
            # Assign this crop to zones
            st.markdown("---")
            st.markdown("### Assign to Zones")
            zones = st.multiselect(
                "Select zones to assign this crop:",
                options=["Zone 1", "Zone 2", "Zone 3", "Zone 4"],
                default=[zone for zone, data in st.session_state.zone_data.items() if data['crop'] == selected_crop]
            )
            
            if st.button("Update Zone Crops"):
                for zone in zones:
                    st.session_state.zone_data[zone]['crop'] = selected_crop
                st.success(f"Updated {len(zones)} zone(s) with {selected_crop}")

# --- 7. NOTIFICATIONS PAGE ---
def notifications_page():
    st.markdown("<h2>Notifications & Alerts</h2>", unsafe_allow_html=True)
    
    # Generate sample notifications based on zone status
    notifications = []
    
    for zone_name, data in st.session_state.zone_data.items():
        if data['water_needed']:
            notifications.append({
                'type': 'warning',
                'message': f"💧 {zone_name} needs water (Current: {data['soil_moisture']}%, Target: {data['target_moisture']}%)",
                'time': "2 hours ago"
            })
        
        if data['temperature'] > CROP_KNOWLEDGE[data['crop']]['temp_range'][1]:
            notifications.append({
                'type': 'warning',
                'message': f"🌡️ {zone_name} temperature is high ({data['temperature']}°C)",
                'time': "1 hour ago"
            })
        
        if data['humidity'] < CROP_KNOWLEDGE[data['crop']]['humidity_range'][0]:
            notifications.append({
                'type': 'info',
                'message': f"💨 {zone_name} humidity is low ({data['humidity']}%)",
                'time': "3 hours ago"
            })
    
    # Add a sample "plant ready" notification
    notifications.append({
        'type': 'success',
        'message': "✅ Ginger in Zone 2 is ready for harvest",
        'time': "1 day ago"
    })
    
    if not notifications:
        st.markdown(
            """
            <div class="notification success">
                🎉 All systems are operating normally! No alerts at this time.
            </div>
            """, 
            unsafe_allow_html=True
        )
    else:
        for notification in notifications:
            st.markdown(
                f"""
                <div class="notification {notification['type']}">
                    <div>{notification['message']}</div>
                    <div style="font-size: 0.8rem; opacity: 0.7;">{notification['time']}</div>
                </div>
                """, 
                unsafe_allow_html=True
            )

# --- 8. PROFILE PAGE ---
def profile_page():
    st.markdown("<h2>Farmer Profile</h2>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.image("https://cdn-icons-png.flaticon.com/512/3135/3135715.png", width=150)
        st.markdown("### Rajesh Kumar")
        st.markdown("Sikkim, Northeast India")
        st.markdown("📞 +91 98765 43210")
        
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    
    with col2:
        st.markdown("### Farm Summary")
        
        # Farm statistics
        total_zones = len(st.session_state.zone_data)
        zones_needing_water = sum(1 for data in st.session_state.zone_data.values() if data['water_needed'])
        optimal_zones = total_zones - zones_needing_water
        
        st.metric("Total Zones", total_zones)
        st.metric("Zones Needing Water", zones_needing_water)
        st.metric("Optimal Zones", optimal_zones)
        
        st.markdown("### Settings")
        
        # Notification preferences
        st.checkbox("Email alerts for water needs", value=True)
        st.checkbox("SMS alerts for critical issues", value=True)
        st.checkbox("Push notifications", value=True)
        
        if st.button("Save Settings", use_container_width=True):
            st.success("Settings updated successfully!")

# --- 9. JAVASCRIPT FOR ZONE SELECTION ---
st.markdown(
    """
    <script>
    function setZone(zoneName) {
        window.parent.postMessage({
            type: 'streamlit:setComponentValue',
            value: zoneName
        }, '*');
    }
    </script>
    """,
    unsafe_allow_html=True
)

# Handle zone selection from JavaScript
if 'zone_selected' in st.query_params:
    st.session_state.current_zone = st.query_params['zone_selected']

# --- 10. MAIN APP LOGIC ---
if not st.session_state.logged_in:
    login_page()
else:
    main_dashboard()
