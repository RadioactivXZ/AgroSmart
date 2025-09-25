from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, Boolean, String, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import os # Used to read environment variables

# --- 1. DATABASE SETUP ---
# Reads the secure database connection string from an environment variable.
# This is the standard practice for production applications.
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./default_local.db")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DATABASE MODELS ---
# Defines the structure of the 'zones' table.
class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    crop = Column(String, default="Unknown")
    target_moisture = Column(Float, default=55.0)
    manual_water_pending = Column(Boolean, default=False)

# Defines the structure of the 'sensor_readings' table.
class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    soil_moisture = Column(Float)
    is_raining = Column(Boolean)

# --- Function to initialize the database ---
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Check if zones have been created, if not, create them.
        inspector = inspect(engine)
        if inspector.has_table("zones"):
            for i in range(1, 5):
                zone_name = f"Zone {i}"
                exists = db.query(Zone).filter(Zone.name == zone_name).first()
                if not exists:
                    db.add(Zone(id=i, name=zone_name))
            db.commit()
    finally:
        db.close()

# --- 3. PYDANTIC MODELS (API Data Validation) ---
class SensorData(BaseModel):
    temperature: float
    humidity: float
    soil_moisture: float
    is_raining: bool

class ZoneResponse(BaseModel):
    pump_on: bool
    message: str

# --- 4. FASTAPI APP INITIALIZATION ---
app = FastAPI(title="AgroSmart API", version="1.2.0")

# Add CORS middleware to allow the frontend to communicate with this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, you would restrict this to your Streamlit app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run the database setup function when the application starts
@app.on_event("startup")
def on_startup():
    setup_database()

# Dependency function to get a database session for each API request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 5. API ENDPOINTS ---
@app.post("/update/{zone_id}", response_model=ZoneResponse, tags=["ESP32"])
def update_sensor_data(zone_id: int, data: SensorData, db: Session = Depends(get_db)):
    """
    Receives sensor data from the ESP32, saves it, and decides if the pump should be turned on.
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    # Create and save the new sensor reading
    db_reading = SensorReading(zone_id=zone_id, **data.dict())
    db.add(db_reading)

    # Determine if the pump should be on
    auto_water_needed = data.soil_moisture < zone.target_moisture and not data.is_raining
    manual_water_requested = zone.manual_water_pending
    pump_on = auto_water_needed or manual_water_requested

    # If this was a manual request, reset the flag
    if manual_water_requested:
        zone.manual_water_pending = False

    db.commit()
    return {"pump_on": pump_on, "message": "Data received and processed"}

@app.post("/manual_water/{zone_id}", tags=["Frontend"])
def request_manual_water(zone_id: int, db: Session = Depends(get_db)):
    """
    Receives a manual watering request from the frontend and sets a flag in the database.
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone.manual_water_pending = True
    db.commit()
    return {"message": f"Manual watering for {zone.name} has been scheduled."}

@app.get("/zones", tags=["Frontend"])
def get_all_zones_status(db: Session = Depends(get_db)):
    """
    Provides the latest sensor data and configuration for all zones to the frontend.
    """
    zone_statuses = {}
    zones = db.query(Zone).all()
    for zone in zones:
        latest_reading = db.query(SensorReading).filter(SensorReading.zone_id == zone.id).order_by(SensorReading.timestamp.desc()).first()

        if latest_reading:
            zone_statuses[zone.name] = {
                "crop": zone.crop,
                "target_moisture": zone.target_moisture,
                "soil_moisture": latest_reading.soil_moisture,
                "temperature": latest_reading.temperature,
                "humidity": latest_reading.humidity,
                "last_updated": latest_reading.timestamp.isoformat()
            }
        else:
            # Provide default data if no readings exist for this zone yet
            zone_statuses[zone.name] = {
                "crop": zone.crop,
                "target_moisture": zone.target_moisture,
                "soil_moisture": 0,
                "temperature": 0,
                "humidity": 0,
                "last_updated": "N/A"
            }
    return zone_statuses

@app.get("/health", tags=["System"])
def health_check():
    """A simple endpoint that Render can use to check if the app is live."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}
