from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, String
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os

# --- Database Setup ---
DATABASE_URL = "sqlite:///./farm_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Define the database table model
class SensorReadingDB(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    soil_moisture = Column(Float)

# Create the database and table if they don't exist
if not os.path.exists("./farm_data.db"):
    Base.metadata.create_all(bind=engine)


# --- Pydantic Models for Data Validation ---
class SensorData(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float

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
def update_sensor_data(zone_id: int, data: SensorData, db: SessionLocal = Depends(get_db)):
    """
    Endpoint for the ESP32 to post new sensor data.
    """
    if not (1 <= zone_id <= 4):
        raise HTTPException(status_code=400, detail="Zone ID must be between 1 and 4")

    # Save the new reading to the database
    db_reading = SensorReadingDB(
        zone_id=zone_id,
        temperature=data.temperature,
        humidity=data.humidity,
        soil_moisture=data.soil_moisture
    )
    db.add(db_reading)
    db.commit()

    # Simple logic for "Smart Water" - you can make this more complex
    # This is a placeholder for the logic in your Streamlit app.
    # The ESP32 code itself will handle manual watering based on this response.
    # We will just return pump_on: False for now, as the Streamlit App handles the watering logic.
    return {"pump_on": False, "message": "Data received."}

@app.get("/zones")
def get_all_zone_data(db: SessionLocal = Depends(get_db)):
    """
    Endpoint for the Streamlit frontend to get the latest data for all zones.
    """
    latest_data = {}
    for i in range(1, 5):
        reading = db.query(SensorReadingDB).filter(SensorReadingDB.zone_id == i).order_by(SensorReadingDB.timestamp.desc()).first()
        if reading:
            latest_data[f"Zone {i}"] = {
                'soil_moisture': reading.soil_moisture,
                'temperature': reading.temperature,
                'humidity': reading.humidity,
                'last_updated': reading.timestamp.isoformat()
            }
        else:
             # Provide default data if no reading exists yet
            latest_data[f"Zone {i}"] = {
                'soil_moisture': 0, 'temperature': 0, 'humidity': 0, 'last_updated': 'N/A'
            }
    return latest_data

@app.post("/manual_water/{zone_id}")
def trigger_manual_water(zone_id: int):
    """
    This is a placeholder endpoint. In a real system, this would trigger a push notification
    or set a flag in a database that the ESP32 would check. For this project, the ESP32's
    internal logic handles the watering after it gets a command.
    """
    print(f"Manual water command received for Zone {zone_id}")
    # In a more advanced setup, you'd save this command to the database.
    # The ESP32's POST to /update would then get a response telling it to water.
    return {"message": f"Watering command for Zone {zone_id} has been acknowledged."}
