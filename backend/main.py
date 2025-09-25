from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, Float, DateTime, Boolean, String, inspect
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

# --- 1. DATABASE SETUP ---
# This will create a farm_data.db file in Render's persistent disk storage.
DATABASE_URL = "sqlite:///./farm_data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DATABASE MODELS ---
# Stores the configuration and state for each zone.
class Zone(Base):
    __tablename__ = "zones"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    crop = Column(String, default="Unknown")
    target_moisture = Column(Float, default=55.0)
    manual_water_pending = Column(Boolean, default=False)

# Stores every sensor reading received from the ESP32.
class SensorReading(Base):
    __tablename__ = "sensor_readings"
    id = Column(Integer, primary_key=True, index=True)
    zone_id = Column(Integer, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    temperature = Column(Float)
    humidity = Column(Float)
    soil_moisture = Column(Float)
    is_raining = Column(Boolean)

# Create tables and initialize zones if they don't exist
def setup_database():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
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

# --- 4. FASTAPI APP ---
app = FastAPI(title="AgroSmart API", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# Setup the database on startup
@app.on_event("startup")
def on_startup():
    setup_database()

# Dependency for getting a DB session
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
    Called by the ESP32 to post sensor data. Saves the data and responds
    with a command on whether to turn the water pump on.
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    db_reading = SensorReading(zone_id=zone_id, **data.dict())
    db.add(db_reading)

    auto_water_needed = data.soil_moisture < zone.target_moisture and not data.is_raining
    manual_water_requested = zone.manual_water_pending
    pump_on = auto_water_needed or manual_water_requested

    if manual_water_requested:
        zone.manual_water_pending = False

    db.commit()
    return {"pump_on": pump_on, "message": "Data received"}

@app.post("/manual_water/{zone_id}", tags=["Frontend"])
def request_manual_water(zone_id: int, db: Session = Depends(get_db)):
    """
    Called by the frontend to trigger a manual watering cycle. Sets a flag
    in the database that the ESP32 will act upon on its next update.
    """
    zone = db.query(Zone).filter(Zone.id == zone_id).first()
    if not zone:
        raise HTTPException(status_code=404, detail="Zone not found")

    zone.manual_water_pending = True
    db.commit()
    return {"message": f"Manual watering for {zone.name} is scheduled."}

@app.get("/zones", tags=["Frontend"])
def get_all_zones_status(db: Session = Depends(get_db)):
    """
    Called by the frontend to get the latest status of all zones.
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
    """Simple health check endpoint to confirm the API is running."""
    return {"status": "healthy"}

