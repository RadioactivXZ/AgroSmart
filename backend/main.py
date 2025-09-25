from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

# --- Database Setup ---
DATABASE_URL = "sqlite:///./farm_data.db" # This is fine for Render/Fly.io
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the database table model
class SensorReadingDB(Base):
    _tablename_ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    soil_moisture = Column(Float)
    is_raining = Column(Boolean) # <-- FIX #1: Added the missing database column

# Create the database and table if they don't exist
Base.metadata.create_all(bind=engine)


# --- Pydantic Models for Data Validation ---
class SensorData(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float
    is_raining: bool # <-- FIX #2: Added the missing field to the validation model

class PumpControlResponse(BaseModel):
    pump_on: bool
    message: str

# --- FastAPI App ---
app = FastAPI(title="AgroSmart API")

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.post("/update/{zone_id}", response_model=PumpControlResponse)
def update_sensor_data(zone_id: int, data: SensorData, db: Session = Depends(get_db)):
    if not (1 <= zone_id <= 4):
        raise HTTPException(status_code=400, detail="Zone ID must be between 1 and 4")

    # Save the new reading to the database
    db_reading = SensorReadingDB(
        zone_id=zone_id,
        temperature=data.temperature,
        humidity=data.humidity,
        soil_moisture=data.soil_moisture,
        is_raining=data.is_raining # <-- FIX #3: Added the logic to save the rain data
    )
    db.add(db_reading)
    db.commit()

    # Placeholder logic for pump control
    return {"pump_on": False, "message": "Data received."}

@app.get("/zones")
def get_all_zone_data(db: Session = Depends(get_db)):
    latest_data = {}
    for i in range(1, 5):
        reading = db.query(SensorReadingDB).filter(SensorReadingDB.zone_id == i).order_by(SensorReadingDB.timestamp.desc()).first()
        if reading:
            latest_data[f"Zone {i}"] = {
                'soil_moisture': reading.soil_moisture,
                'temperature': reading.temperature,
                'humidity': reading.humidity,
                'is_raining': reading.is_raining, # Also good to add this to the response
                'last_updated': reading.timestamp.isoformat()
            }
        else:
            latest_data[f"Zone {i}"] = {
                'soil_moisture': 0, 'temperature': 0, 'humidity': 0, 'is_raining': False, 'last_updated': 'N/A'
            }
    return latest_data

# The manual_water endpoint is fine as is.
@app.post("/manual_water/{zone_id}")
def trigger_manual_water(zone_id: int):
    print(f"Manual water command received for Zone {zone_id}")
    return {"message": f"Watering command for Zone {zone_id} has been acknowledged."}
