from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime
import time

app = FastAPI(title="AgroSmart Backend", description="Backend for AgroSmart IoT Farm Management", version="1.0.0")

# CORS Middleware to allow requests from Streamlit frontend (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to your frontend URL, e.g., ["https://your-streamlit-app.streamlit.app"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for zone data (use a database like SQLite for persistence in production)
zone_data: Dict[str, Dict[str, Any]] = {
    "1": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Ginger", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
    "2": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Large Cardamom", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
    "3": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Mandarin Orange", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
    "4": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Ginger", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
}

# Pydantic models for request/response validation
class SensorData(BaseModel):
    soil_moisture: float
    temperature: float
    humidity: float
    is_raining: bool

class WaterCommand(BaseModel):
    amount: Optional[int] = 0  # Liters, for manual watering simulation

class ZoneResponse(BaseModel):
    pump_on: bool
    message: str = "OK"

# Hardcoded crops per zone (can be made dynamic or from DB)
CROPS = {
    "1": "Ginger",
    "2": "Large Cardamom",
    "3": "Mandarin Orange",
    "4": "Ginger",
}

# Default target moisture (can be per crop or configurable)
DEFAULT_TARGET_MOISTURE = 55

# --- ENDPOINTS ---

@app.get("/zones")
async def get_all_zones():
    """
    Endpoint for frontend to fetch all zone data.
    Returns computed data including water_needed, status, etc.
    """
    computed_data = {}
    for zone_id, data in zone_data.items():
        zone_name = f"Zone {zone_id}"
        computed_data[zone_name] = {
            "temperature": data["temperature"],
            "humidity": data["humidity"],
            "soil_moisture": data["soil_moisture"],
            "crop": data["crop"],
            "target_moisture": data["target_moisture"],
            "water_needed": data["water_needed"],
            "status": data["status"],
            "manual_water_level": data["manual_water_level"],
            "last_updated": data["last_updated"],
        }
    return computed_data

@app.post("/zones/{zone_id}", response_model=ZoneResponse)
async def update_zone_data(zone_id: str, sensor_data: SensorData):
    """
    Endpoint for ESP32 to POST sensor data for a specific zone.
    Computes if watering is needed and responds with pump_on decision.
    """
    if zone_id not in zone_data:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Update raw sensor data
    zone_data[zone_id]["soil_moisture"] = sensor_data.soil_moisture
    zone_data[zone_id]["temperature"] = sensor_data.temperature
    zone_data[zone_id]["humidity"] = sensor_data.humidity
    zone_data[zone_id]["is_raining"] = sensor_data.is_raining
    zone_data[zone_id]["last_updated"] = datetime.now().isoformat()

    # Set crop if not already set
    if "crop" not in zone_data[zone_id] or not zone_data[zone_id]["crop"]:
        zone_data[zone_id]["crop"] = CROPS.get(zone_id, "Unknown")

    # Compute water needed: soil_moisture < target_moisture
    target_moisture = zone_data[zone_id].get("target_moisture", DEFAULT_TARGET_MOISTURE)
    water_needed = sensor_data.soil_moisture < target_moisture
    zone_data[zone_id]["water_needed"] = water_needed

    # Compute status
    zone_data[zone_id]["status"] = "Needs Attention" if water_needed else "Optimal"

    # Decide pump_on: auto (if water_needed and not raining) OR manual pending
    auto_water = water_needed and not sensor_data.is_raining
    manual_water = zone_data[zone_id].get("manual_water_pending", False)
    pump_on = auto_water or manual_water

    # If manual, reset the flag after responding
    if manual_water:
        zone_data[zone_id]["manual_water_pending"] = False

    # Log for debugging (in production, use proper logging)
    print(f"Zone {zone_id}: water_needed={water_needed}, raining={sensor_data.is_raining}, manual={manual_water}, pump_on={pump_on}")

    return ZoneResponse(pump_on=pump_on, message=f"Zone {zone_id} updated")

@app.post("/zones/{zone_id}/water")
async def manual_water_zone(zone_id: str, command: WaterCommand):
    """
    Endpoint for frontend to trigger manual watering.
    Sets a flag that the next ESP32 POST will honor by turning pump_on=true.
    Updates manual_water_level.
    """
    if zone_id not in zone_data:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone_data[zone_id]["manual_water_level"] = command.amount
    zone_data[zone_id]["manual_water_pending"] = True
    zone_data[zone_id]["water_needed"] = True  # Force water_needed for display
    zone_data[zone_id]["status"] = "Watering Requested"

    print(f"Manual water request for Zone {zone_id}: {command.amount} liters")
    return {"message": f"Manual watering requested for Zone {zone_id}. Next sensor sync will activate pump."}

@app.get("/health")
async def health_check():
    """Simple health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# For development/testing, add a way to reset data
@app.post("/reset")
async def reset_data():
    """Reset all zone data (for testing only)."""
    global zone_data
    zone_data = {
        "1": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Ginger", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
        "2": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Large Cardamom", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
        "3": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Mandarin Orange", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
        "4": {"temperature": 0, "humidity": 0, "soil_moisture": 0, "is_raining": False, "last_updated": None, "crop": "Ginger", "target_moisture": 55, "water_needed": False, "status": "Optimal", "manual_water_level": 0, "manual_water_pending": False},
    }
    return {"message": "Data reset"}

if _name_ == "_main_":
    uvicorn.run(app, host="0.0.0.0", port=8000)
