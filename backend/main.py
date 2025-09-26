from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Allow cross-origin requests (for Streamlit frontend)

# --- DATABASE CONFIGURATION ---
DB_URL = os.environ.get("DATABASE_URL", "sqlite:///agrosmart.db")
app.config['SQLALCHEMY_DATABASE_URI'] = DB_URL
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- DATABASE MODELS ---
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
            'zone_id': self.zone_id,
            'soil_moisture': self.soil_moisture,
            'temperature': self.temperature,
            'humidity': self.humidity,
            'is_raining': self.is_raining,
            'timestamp': self.timestamp.isoformat(),
            'pump_activated': self.pump_activated
        }

# Optional: Track pump status separately
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

# Create tables
with app.app_context():
    db.create_all()

# --- ROUTES ---
@app.route('/<int:zone_id>', methods=['POST'])
def receive_sensor_data(zone_id):
    try:
        data = request.get_json()
        required_fields = ['soil_moisture', 'temperature', 'humidity', 'is_raining']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing field: {field}'}), 400

        sensor_data = SensorData(
            zone_id=zone_id,
            soil_moisture=data['soil_moisture'],
            temperature=data['temperature'],
            humidity=data['humidity'],
            is_raining=data['is_raining']
        )

        # Determine if pump should activate
        pump_decision = determine_pump_activation(data)
        sensor_data.pump_activated = pump_decision

        db.session.add(sensor_data)
        db.session.commit()

        # Update pump control table
        pump_control = PumpControl.query.filter_by(zone_id=zone_id).first()
        if not pump_control:
            pump_control = PumpControl(zone_id=zone_id)
            db.session.add(pump_control)

        pump_control.is_active = pump_decision
        if pump_decision:
            pump_control.last_activated = datetime.utcnow()

        db.session.commit()

        return jsonify({'pump_on': pump_decision, 'message': f'Data received for zone {zone_id}'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def determine_pump_activation(data):
    if data['is_raining']:
        return False
    if data['soil_moisture'] > 60:
        return False
    if data['soil_moisture'] < 30 and data['temperature'] < 40:
        return True
    if data['soil_moisture'] < 20:
        return True
    return False


@app.route('/api/data', methods=['GET'])
def get_sensor_data():
    zones_data = {}
    for zone_id in range(1, 5):
        latest_data = SensorData.query.filter_by(zone_id=zone_id).order_by(SensorData.timestamp.desc()).first()
        if latest_data:
            zones_data[f'Zone {zone_id}'] = latest_data.to_dict()
        else:
            # If no data yet, return default values
            zones_data[f'Zone {zone_id}'] = {
                "soil_moisture": 0,
                "temperature": 0,
                "humidity": 0,
                "is_raining": False,
                "pump_activated": False
            }
    return jsonify(zones_data)


@app.route('/', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy', 'message': 'AgroSmart Flask Backend is running'})


# No app.run() needed; Render will use Gunicorn
