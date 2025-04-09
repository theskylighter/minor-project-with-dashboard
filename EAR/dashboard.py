from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO
import json
import os
import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'drowsiness_detection_secret'
socketio = SocketIO(app)

ALERTS_FILE = "driver_alerts.json"
MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

# Track current driver status
current_driver_status = {
    "status": "Active",
    "location": None,
    "last_update": None
}

def get_alerts():
    """Load alerts from JSON file"""
    if os.path.exists(ALERTS_FILE):
        with open(ALERTS_FILE, "r") as f:
            try:
                return json.load(f)
            except:
                return []
    return []

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html', 
                         alerts=get_alerts(), 
                         current_status=current_driver_status,
                         maps_api_key=MAPS_API_KEY)

@app.route('/alert', methods=['POST'])
def receive_alert():
    """Endpoint to receive alerts from the drowsiness detection system"""
    alert_data = request.json
    current_driver_status["status"] = alert_data.get("status", "Unknown")
    
    # Broadcast new alert to all connected clients
    socketio.emit('new_alert', alert_data)
    
    return jsonify({"status": "success"})

@app.route('/location_update', methods=['POST'])
def location_update():
    """Endpoint to receive continuous location updates"""
    data = request.json
    current_driver_status["location"] = data
    current_driver_status["last_update"] = datetime.datetime.now().isoformat()
    
    # Broadcast location update to all connected clients
    socketio.emit('location_update', {
        "location": data,
        "status": current_driver_status["status"],
        "timestamp": current_driver_status["last_update"]
    })
    
    return jsonify({"status": "success"})

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Create static directory if it doesn't exist
    if not os.path.exists('static'):
        os.makedirs('static')
    
    socketio.run(app, debug=True)