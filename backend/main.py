from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import os

app = Flask(__name__) # <-- FIX #1: Corrected from _name_ to __name__

# --- DATABASE CONFIGURATION ---
# Reads the secure database URL from an environment variable provided by Render.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///agrosmart.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
# (Your database models remain exactly the same)
class SensorData(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, nullable=False)
    soil_moisture = db.Column(db.Float, nullable=False)
    temperature = db.Column(db.Float, nullable=False)
    humidity = db.Column(db.Float, nullable=False)
    is_raining = db.Column(db.Boolean, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    pump_activated = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return { 'id': self.id, 'zone_id': self.zone_id, 'soil_moisture': self.soil_moisture, 'temperature': self.temperature, 'humidity': self.humidity, 'is_raining': self.is_raining, 'timestamp': self.timestamp.isoformat(), 'pump_activated': self.pump_activated }

class PumpControl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    last_activated = db.Column(db.DateTime)
    auto_mode = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return { 'zone_id': self.zone_id, 'is_active': self.is_active, 'last_activated': self.last_activated.isoformat() if self.last_activated else None, 'auto_mode': self.auto_mode }

# --- DATABASE INITIALIZATION ---
# This command ensures tables are created when the app starts.
with app.app_context():
    db.create_all()

# --- API ROUTES ---
# (All your API routes remain exactly the same)
@app.route('/<int:zone_id>', methods=['POST'])
def receive_sensor_data(zone_id):
    try:
        data = request.get_json()
        required_fields = ['soil_moisture', 'temperature', 'humidity', 'is_raining']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        sensor_data = SensorData(zone_id=zone_id, soil_moisture=data['soil_moisture'], temperature=data['temperature'], humidity=data['humidity'], is_raining=data['is_raining'])
        pump_decision = determine_pump_activation(zone_id, data)
        sensor_data.pump_activated = pump_decision
        
        db.session.add(sensor_data)
        db.session.commit()
        
        pump_control = PumpControl.query.filter_by(zone_id=zone_id).first()
        if not pump_control:
            pump_control = PumpControl(zone_id=zone_id)
            db.session.add(pump_control)
        
        if pump_decision:
            pump_control.is_active = True
            pump_control.last_activated = datetime.utcnow()
        else:
            pump_control.is_active = False
            
        db.session.commit()
        
        return jsonify({ 'pump_on': pump_decision, 'message': f'Data received for zone {zone_id}' })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def determine_pump_activation(zone_id, data):
    if data['is_raining']: return False
    if data['soil_moisture'] > 60: return False
    if data['soil_moisture'] < 30 and data['temperature'] < 40: return True
    if data['soil_moisture'] < 20: return True
    return False

@app.route('/api/data', methods=['GET'])
def get_sensor_data():
    zones_data = {}
    for zone_id in range(1, 5):
        latest_data = SensorData.query.filter_by(zone_id=zone_id).order_by(SensorData.timestamp.desc()).first()
        if latest_data:
            zones_data[f'Zone {zone_id}'] = latest_data.to_dict()
    return jsonify(zones_data)
    
@app.route('/', methods=['GET'])
def health_check():
    return jsonify({ 'status': 'healthy', 'message': 'AgroSmart Flask Backend is running' })

# FIX #2: The app.run() block is removed. Gunicorn will run the app.
