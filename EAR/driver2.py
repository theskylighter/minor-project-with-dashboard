import cv2
import numpy as np
import dlib
from imutils import face_utils
import winsound
import time
import os
import json
import datetime
from geopy.geocoders import Nominatim
import threading
import requests
import subprocess

# Driver information - in a real application, this would be configured or input
DRIVER_INFO = {
    "name": "John Doe",
    "id": "DRV12345",
    "vehicle": "TN-01-AB-1234",
    "phone": "+1-555-123-4567"  # Added driver phone number
}

# Alert configuration
SLEEP_ALERT_THRESHOLD = 5  # seconds - alert after this many seconds of sleeping
DROWSY_ALERT_THRESHOLD = 7  # seconds - alert after this many seconds of drowsiness
alert_start_time = None
drowsy_alert_start_time = None
alert_sent = False
drowsy_alert_sent = False

# Location tracking setup
geolocator = Nominatim(user_agent="driver_drowsiness_detector")
current_location = {"latitude": 0, "longitude": 0, "address": "Unknown"}

def get_windows_location():
    """Get location using Windows Location API via PowerShell"""
    try:
        # Run PowerShell script with ExecutionPolicy Bypass
        result = subprocess.run(
            ['powershell.exe', '-ExecutionPolicy', 'Bypass', '-File', './get_location.ps1'],
            capture_output=True,
            text=True
        )
        
        # Parse the JSON output
        location_data = json.loads(result.stdout)
        
        if location_data.get('error') is None:
            return location_data['latitude'], location_data['longitude']
        else:
            print(f"Error getting location: {location_data['error']}")
            return None, None
    except Exception as e:
        print(f"Error running PowerShell script: {e}")
        return None, None

def update_location():
    """Get real location from Windows Location API"""
    try:
        latitude, longitude = get_windows_location()
        
        if latitude is not None and longitude is not None:
            current_location["latitude"] = latitude
            current_location["longitude"] = longitude
            
            # Get address using geocoding
            try:
                location = geolocator.reverse(f"{latitude}, {longitude}", exactly_one=True)
                current_location["address"] = location.address if location else "Unknown"
                print(f"Location updated: {current_location['address']}")
                
                # Send location update to dashboard
                try:
                    requests.post("http://localhost:5000/location_update", 
                                json=current_location,
                                timeout=1)
                except:
                    print("Could not send location update to dashboard")
                    
            except Exception as e:
                print(f"Error getting address: {e}")
                current_location["address"] = f"Location at {latitude}, {longitude}"
        else:
            print("Could not get location from Windows Location API")
    except Exception as e:
        print(f"Error updating location: {e}")

# Start a thread to update location periodically
def location_updater():
    while True:
        update_location()
        time.sleep(5)  # Update every 5 seconds

location_thread = threading.Thread(target=location_updater, daemon=True)
location_thread.start()

# Alert logging system
ALERTS_FILE = "driver_alerts.json"

def log_alert(status, duration):
    """Log an alert to the JSON file and send to dashboard"""
    try:
        alert_data = {
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "driver": DRIVER_INFO,
            "status": status,
            "duration": duration,
            "location": current_location
        }
        
        # Load existing alerts or create new list
        if os.path.exists(ALERTS_FILE):
            with open(ALERTS_FILE, "r") as f:
                alerts = json.load(f)
        else:
            alerts = []
        
        # Insert new alert at the beginning of the list (instead of appending)
        alerts.insert(0, alert_data)
        with open(ALERTS_FILE, "w") as f:
            json.dump(alerts, f, indent=4)
        
        # Send alert to web dashboard if it's running
        try:
            requests.post("http://localhost:5000/alert", json=alert_data, timeout=1)
        except:
            pass  # Dashboard might not be running, that's OK
            
        print(f"Alert logged: {status} - {current_location['address']}")
    except Exception as e:
        print(f"Error logging alert: {e}")

# Initialize webcam with higher FPS
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FPS, 30)  # Request 30 FPS
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Smaller resolution for faster processing
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

detector = dlib.get_frontal_face_detector()
predictor = dlib.shape_predictor("./shape_predictor_68_face_landmarks.dat")

# Calibration variables
awake_ear = None
drowsy_ear = None
sleep_ear = None

# Constants for state changes - reduced for faster response
STATE_CHANGE_FRAMES = 3  # Reduced from 6 to 3 frames
FRAME_BUFFER_SIZE = 5  # Keep track of last 5 EAR values for smoothing

# Buffer for EAR values to smooth out detection
ear_buffer = []

def smooth_ear(ear_value):
    """Smooth EAR values using moving average"""
    global ear_buffer
    ear_buffer.append(ear_value)
    if len(ear_buffer) > FRAME_BUFFER_SIZE:
        ear_buffer.pop(0)
    return sum(ear_buffer) / len(ear_buffer)

def compute(ptA, ptB):
    return np.linalg.norm(ptA - ptB)

def get_ear(landmarks):
    left = compute(landmarks[37], landmarks[41]) + compute(landmarks[38], landmarks[40])
    right = compute(landmarks[43], landmarks[47]) + compute(landmarks[44], landmarks[46])
    down_left = compute(landmarks[36], landmarks[39])
    down_right = compute(landmarks[42], landmarks[45])
    return (left + right) / (2.0 * (down_left + down_right))

def calibrate_phase(message, duration=10):
    start_time = time.time()
    ear_values = []
    
    # Get initial frame to determine dimensions
    ret, frame = cap.read()
    if not ret:
        return 0.2  # Default fallback
        
    height, width = frame.shape[:2]
    
    while time.time() - start_time < duration:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip frame horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        # Calculate remaining time
        remaining = duration - int(time.time() - start_time)
        
        # Split message into multiple lines if too long
        words = message.split()
        lines = []
        current_line = []
        
        for word in words:
            current_line.append(word)
            # Check if current line would be too long
            test_line = ' '.join(current_line)
            text_size = cv2.getTextSize(test_line, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
            if text_size[0] > width - 100:  # Leave 50px margin on each side
                lines.append(' '.join(current_line[:-1]))
                current_line = [word]
        
        if current_line:
            lines.append(' '.join(current_line))
        
        # Draw text with proper spacing
        y_position = 50
        for line in lines:
            cv2.putText(frame, line, (30, y_position), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            y_position += 30
        
        # Add time remaining below instructions
        y_position += 10  # Add some space
        cv2.putText(frame, f"Time left: {remaining} seconds", 
                   (30, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Calculate and display current EAR value
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = detector(gray)
        for face in faces:
            landmarks = predictor(gray, face)
            landmarks = face_utils.shape_to_np(landmarks)
            ear = get_ear(landmarks)
            ear_values.append(ear)
            
            # Show EAR value below time remaining
            y_position += 30
            cv2.putText(frame, f"EAR: {ear:.2f}", 
                       (30, y_position), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
        
        cv2.imshow("Calibration", frame)
        if cv2.waitKey(1) == 27:
            break
    
    # Display completion message
    if ear_values:
        completion_frame = np.zeros((height, width, 3), dtype=np.uint8)
        messages = [
            "Calibration Complete!",
            f"Average EAR: {np.mean(ear_values):.2f}"
        ]
        
        y_position = height // 3
        for msg in messages:
            text_size = cv2.getTextSize(msg, cv2.FONT_HERSHEY_SIMPLEX, 1, 2)[0]
            x_position = (width - text_size[0]) // 2
            cv2.putText(completion_frame, msg, (x_position, y_position),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            y_position += 50
        
        cv2.imshow("Calibration", completion_frame)
        cv2.waitKey(1000)  # Show completion message for 1 second
        
    return np.mean(ear_values) if ear_values else 0.2  # Default fallback

# Calibration process
awake_ear = calibrate_phase("Look straight with your eyes open for calibration...")
drowsy_ear = calibrate_phase("Half-close your eyes (simulate drowsiness)...")
sleep_ear = calibrate_phase("Close your eyes completely...")

cv2.destroyAllWindows()

sleep = 0
drowsy = 0
active = 0
status = ""
color = (0, 0, 0)
beep_played = False
prev_time = time.time()
fps = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break
        
    # Calculate FPS
    current_time = time.time()
    fps = 1 / (current_time - prev_time)
    prev_time = current_time
    
    # Flip frame horizontally for mirror effect
    frame = cv2.flip(frame, 1)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = detector(gray)
    
    height, width = frame.shape[:2]
    y_position = 50
    
    # Display FPS
    cv2.putText(frame, f"FPS: {fps:.1f}", (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
    
    # Display status with background for better visibility
    status_size = cv2.getTextSize(status, cv2.FONT_HERSHEY_SIMPLEX, 1.2, 3)[0]
    status_x = (width - status_size[0]) // 2
    
    # Draw semi-transparent background for text
    overlay = frame.copy()
    cv2.rectangle(overlay, 
                 (status_x - 10, y_position - 40),
                 (status_x + status_size[0] + 10, y_position + 10),
                 (0, 0, 0),
                 -1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
    
    # Draw status text
    cv2.putText(frame, status, (status_x, y_position), 
                cv2.FONT_HERSHEY_SIMPLEX, 1.2, color, 3)
    
    for face in faces:
        landmarks = predictor(gray, face)
        landmarks = face_utils.shape_to_np(landmarks)
        ear = get_ear(landmarks)
        
        # Smooth EAR value
        smoothed_ear = smooth_ear(ear)
        
        # Adjusted thresholds with smoothed EAR
        if smoothed_ear >= awake_ear * 0.85:  # Slightly more lenient threshold
            sleep, drowsy = 0, 0
            active += 1
            if active >= STATE_CHANGE_FRAMES:
                status, color, beep_played = "Active :)", (0, 255, 0), False
                active = STATE_CHANGE_FRAMES  # Cap the counter
        elif smoothed_ear < awake_ear * 0.85 and smoothed_ear > sleep_ear * 1.1:  # Better drowsy range between awake and sleep
            sleep, active = 0, 0
            drowsy += 1
            if drowsy >= STATE_CHANGE_FRAMES:
                status, color, beep_played = "Drowsy !", (0, 255, 255), False
                drowsy = STATE_CHANGE_FRAMES  # Cap the counter
                if drowsy_alert_start_time is None:
                    drowsy_alert_start_time = time.time()
                elif time.time() - drowsy_alert_start_time > DROWSY_ALERT_THRESHOLD and not drowsy_alert_sent:
                    log_alert(status, time.time() - drowsy_alert_start_time)
                    drowsy_alert_sent = True
        elif smoothed_ear <= sleep_ear * 1.1:  # Slightly more lenient sleep threshold
            active, drowsy = 0, 0
            sleep += 1
            if sleep >= STATE_CHANGE_FRAMES:
                status, color = "SLEEPING !!!", (0, 0, 255)
                sleep = STATE_CHANGE_FRAMES  # Cap the counter
                if not beep_played:
                    winsound.PlaySound("beep (2).wav", winsound.SND_ASYNC)
                    beep_played = True
                if alert_start_time is None:
                    alert_start_time = time.time()
                elif time.time() - alert_start_time > SLEEP_ALERT_THRESHOLD and not alert_sent:
                    log_alert(status, time.time() - alert_start_time)
                    alert_sent = True
        
        # Reset alert state if active
        if status == "Active :)" and alert_start_time is not None:
            alert_start_time = None
            alert_sent = False
        if status == "Active :)" and drowsy_alert_start_time is not None:
            drowsy_alert_start_time = None
            drowsy_alert_sent = False
        
        # Display EAR values
        y_position += 40
        ear_text = f"EAR: {smoothed_ear:.2f} (Raw: {ear:.2f})"
        ear_size = cv2.getTextSize(ear_text, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2)[0]
        ear_x = (width - ear_size[0]) // 2
        
        # Draw background for EAR value
        cv2.rectangle(frame,
                     (ear_x - 5, y_position - 25),
                     (ear_x + ear_size[0] + 5, y_position + 5),
                     (0, 0, 0),
                     -1)
        cv2.putText(frame, ear_text, (ear_x, y_position),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    cv2.imshow("Driver Drowsiness Detector", frame)
    
    if cv2.waitKey(1) == 27:
        break

cap.release()
cv2.destroyAllWindows()