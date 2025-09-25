from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

# --- 1. DATABASE SETUP ---
# Render uses an ephemeral filesystem, meaning this file will be reset on
# every deploy. For persistent data, you would add a Render Disk.
# For this project, a fresh database on each deploy is acceptable.
DATABASE_URL = "sqlite:///./farm_data.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DATABASE MODEL ---
# This class defines the structure of the 'sensor_readings' table in our database.
class SensorReadingDB(Base):
    # CRITICAL FIX: Changed from '_tablename_' to the correct '__tablename__'
    __tablename__ = "sensor_readings"
    
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    soil_moisture = Column(Float)
    is_raining = Column(Boolean)

# Create the database and the table if it doesn't already exist.
Base.metadata.create_all(bind=engine)


# --- 3. PYDANTIC MODELS (DATA VALIDATION) ---
# These models ensure the data sent from the ESP32 has the correct format and types.
class SensorData(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float
    is_raining: bool

class PumpControlResponse(BaseModel):
    pump_on: bool
    message: str


# --- 4. FASTAPI APP INITIALIZATION ---
app = FastAPI(
    title="AgroSmart API",
    description="API for the AgroSmart irrigation system to receive sensor data and send commands.",
    version="1.0.0"
)

# --- 5. DEPENDENCY for Database Session ---
# This function provides a database session to each API endpoint and ensures
# the session is always closed correctly, even if an error occurs.
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --- 6. API ENDPOINTS ---

@app.post("/update/{zone_id}", response_model=PumpControlResponse, tags=["ESP32"])
def update_sensor_data(zone_id: int, data: SensorData, db: Session = Depends(get_db)):
    """
    Receives sensor data from a specific ESP32 zone, saves it to the
    database, and returns any commands (like turning on a pump).
    """
    if not (1 <= zone_id <= 4):
        raise HTTPException(status_code=400, detail="Zone ID must be between 1 and 4")

    # Create a new record using the database model
    db_reading = SensorReadingDB(
        zone_id=zone_id,
        temperature=data.temperature,
        humidity=data.humidity,
        soil_moisture=data.soil_moisture,
        is_raining=data.is_raining
    )
    db.add(db_reading)
    db.commit()

    # In a future version, you could add logic here to check the moisture level
    # against a target and decide whether to turn the pump on.
    # For now, we will let the frontend handle the logic.
    return {"pump_on": False, "message": "Data successfully received."}


@app.get("/zones", tags=["Frontend"])
def get_all_zone_data(db: Session = Depends(get_db)):
    """
    Provides the most recent sensor reading for all zones to the frontend dashboard.
    """
    latest_data = {}
    for i in range(1, 5):
        # Query the database for the latest record for the current zone
        reading = db.query(SensorReadingDB).filter(SensorReadingDB.zone_id == i).order_by(SensorReadingDB.timestamp.desc()).first()
        
        if reading:
            latest_data[f"Zone {i}"] = {
                'soil_moisture': reading.soil_moisture,
                'temperature': reading.temperature,
                'humidity': reading.humidity,
                'is_raining': reading.is_raining,
                'last_updated': reading.timestamp.isoformat()
            }
        else:
            # Provide default data if no reading for a zone has ever been received
            latest_data[f"Zone {i}"] = {
                'soil_moisture': 0, 'temperature': 0, 'humidity': 0, 'is_raining': False, 'last_updated': 'N/A'
            }
    return latest_data

# The manual_water endpoint can be kept as a placeholder for future functionality.
@app.post("/manual_water/{zone_id}", tags=["Frontend"])
def trigger_manual_water(zone_id: int):
    """
    Placeholder endpoint to acknowledge manual watering commands from the frontend.
    """
    print(f"Manual water command received for Zone {zone_id}")
    return {"message": f"Watering command for Zone {zone_id} has been acknowledged."}
