from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json
import os

app = Flask(_name_)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///agrosmart.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
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
        return {
            'id': self.id,
            'zone_id': self.zone_id,
            'soil_moisture': self.soil_moisture,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'is_raining': self.is_raining,
            'timestamp': self.timestamp.isoformat(),
            'pump_activated': self.pump_activated
        }

class PumpControl(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    zone_id = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=False)
    last_activated = db.Column(db.DateTime)
    auto_mode = db.Column(db.Boolean, default=True)

    def to_dict(self):
        return {
            'zone_id': self.zone_id,
            'is_active': self.is_active,
            'last_activated': self.last_activated.isoformat() if self.last_activated else None,
            'auto_mode': self.auto_mode
        }

# Initialize database
with app.app_context():
    db.create_all()

# API Routes

@app.route('/<int:zone_id>', methods=['POST'])
def receive_sensor_data(zone_id):
    """Receive sensor data from ESP32 and return pump control decision"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['soil_moisture', 'temperature', 'humidity', 'is_raining']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400
        
        # Store sensor data
        sensor_data = SensorData(
            zone_id=zone_id,
            soil_moisture=data['soil_moisture'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            is_raining=data['is_raining']
        )
        
        # Determine if pump should be activated
        pump_decision = determine_pump_activation(zone_id, data)
        sensor_data.pump_activated = pump_decision
        
        db.session.add(sensor_data)
        db.session.commit()
        
        # Update pump control status
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
        
        return jsonify({
            'pump_on': pump_decision,
            'message': f'Data received for zone {zone_id}'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def determine_pump_activation(zone_id, data):
    """Simple logic to determine if pump should be activated"""
    soil_moisture = data['soil_moisture']
    temperature = data['temperature']
    humidity = data['humidity']
    is_raining = data['is_raining']
    
    # Don't water if it's raining
    if is_raining:
        return False
    
    # Don't water if soil is already moist (adjust threshold as needed)
    if soil_moisture > 60:
        return False
    
    # Water if soil is dry and temperature is not too high
    if soil_moisture < 30 and temperature < 40:
        return True
    
    # Water if soil is very dry regardless of temperature
    if soil_moisture < 20:
        return True
    
    return False

@app.route('/api/data', methods=['GET'])
def get_sensor_data():
    """Get latest sensor data for all zones"""
    try:
        # Get latest data for each zone
        zones_data = {}
        for zone_id in range(1, 5):  # Zones 1-4
            latest_data = SensorData.query.filter_by(zone_id=zone_id)\
                .order_by(SensorData.timestamp.desc()).first()
            if latest_data:
                zones_data[f'zone_{zone_id}'] = latest_data.to_dict()
        
        return jsonify(zones_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data/<int:zone_id>', methods=['GET'])
def get_zone_data(zone_id):
    """Get sensor data for a specific zone"""
    try:
        # Get data from last 24 hours
        since = datetime.utcnow() - timedelta(hours=24)
        data = SensorData.query.filter(
            SensorData.zone_id == zone_id,
            SensorData.timestamp >= since
        ).order_by(SensorData.timestamp.desc()).all()
        
        return jsonify([record.to_dict() for record in data])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pump/<int:zone_id>', methods=['POST'])
def manual_pump_control(zone_id):
    """Manual pump control (for testing or manual override)"""
    try:
        data = request.get_json()
        action = data.get('action')  # 'on' or 'off'
        
        pump_control = PumpControl.query.filter_by(zone_id=zone_id).first()
        if not pump_control:
            pump_control = PumpControl(zone_id=zone_id)
            db.session.add(pump_control)
        
        if action == 'on':
            pump_control.is_active = True
            pump_control.last_activated = datetime.utcnow()
            pump_control.auto_mode = False
        elif action == 'off':
            pump_control.is_active = False
            pump_control.auto_mode = False
        
        db.session.commit()
        
        return jsonify({
            'zone_id': zone_id,
            'pump_on': pump_control.is_active,
            'auto_mode': pump_control.auto_mode
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status', methods=['GET'])
def get_system_status():
    """Get overall system status"""
    try:
        # Get pump status for all zones
        pump_status = {}
        for zone_id in range(1, 5):
            pump_control = PumpControl.query.filter_by(zone_id=zone_id).first()
            if pump_control:
                pump_status[f'zone_{zone_id}'] = pump_control.to_dict()
        
        # Get latest sensor readings
        latest_readings = {}
        for zone_id in range(1, 5):
            latest = SensorData.query.filter_by(zone_id=zone_id)\
                .order_by(SensorData.timestamp.desc()).first()
            if latest:
                latest_readings[f'zone_{zone_id}'] = {
                    'soil_moisture': latest.soil_moisture,
                    'temperature': latest.temperature,
                    'humidity': latest.humidity,
                    'is_raining': latest.is_raining,
                    'timestamp': latest.timestamp.isoformat()
                }
        
        return jsonify({
            'pump_status': pump_status,
            'latest_readings': latest_readings,
            'system_time': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'AgroSmart Backend is running',
        'timestamp': datetime.utcnow().isoformat()
    })

if _name_ == '_main_':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
