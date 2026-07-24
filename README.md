# SentinelTrack 🛡️📍

SentinelTrack is a complete anti-theft tracking ecosystem designed to monitor your authorized devices (laptops, mobile phones, and ESP32 hardware) with an emphasis on privacy, security, and AI-driven telemetry analysis.

## Ecosystem Architecture
1. **Django REST API (Backend)**: Handles authentication, device registration, and stores all telemetry (GPS + Battery).
2. **Celery AI Engine**: Asynchronously evaluates incoming telemetry to detect anomalies (speeding, rapid battery drain) and triggers Geofence breach alerts.
3. **React Web Dashboard**: A glassmorphic live map interface to view your active devices in real-time, draw Geofences, and monitor system alerts.
4. **Laptop Tracker**: A lightweight Python script that runs in the background of your PC/Mac to securely transmit its location.
5. **Mobile Tracker (React Native)**: A mobile app utilizing Expo's Background Task Manager to act as an independent tracking node.

---

## Getting Started: How to Use the System

To test the SentinelTrack MVP locally, you need to run three separate components in separate terminal windows.

### 1. Start the Backend API
The backend requires Python and Django to serve the endpoints and manage the database.
Open a terminal, navigate to the backend folder, activate the virtual environment, and run the server:
```powershell
cd Tracker\backend
.\venv\Scripts\Activate.ps1
python manage.py runserver
```
*(The API will now be running on `http://localhost:8000`)*

### 2. Start the Live Web Dashboard
The frontend dashboard is built with Vite, React, and Leaflet maps.
Open a **new** terminal window, navigate to the web dashboard, and start the Vite dev server:
```powershell
cd Tracker\web-dashboard
npm run dev
```
*(You can now open `http://localhost:5173` in your browser. Note: You won't see devices on the map until a tracker connects!)*

### 3. Start a Tracker (Laptop)
To see a device on your live map, we need to generate telemetry data. The Python laptop tracker simulates this.
Open a **third** terminal window, navigate to the laptop-app folder, and start the script:
```powershell
cd Tracker\laptop-app
python laptop_tracker.py
```
*(This script will authenticate as the test user, register your laptop's hostname, and begin sending GPS coordinates every 10 seconds. You will see output in the terminal confirming upload success).*

---

## Testing Features on the Web Dashboard

Once all three components are running, open your web browser to **`http://localhost:5173`**.

1. **Viewing Trackers**: You will immediately see your laptop listed in the "Active Trackers" panel on the right. A green pulsing marker will appear on the map at its simulated GPS coordinates.
2. **Device Details**: Click on the map marker to open a popup showing the exact battery percentage and the timestamp of the last telemetry ping.
3. **Drawing a Geofence**:
   - Click the **`+ Add Geofence`** button on the left sidebar.
   - Your cursor will turn into a crosshair. Click anywhere on the map near your laptop's marker.
   - A blue 500-meter circular geofence will instantly render on the map and securely save to the backend database.
4. **Triggering Alerts**:
   - If the laptop tracker's simulated GPS coordinates suddenly jump outside of the Geofence you just drew, the Celery AI Engine will detect a "Geofence Exit" event.
   - You will see a red notification instantly populate in the **System Alerts** panel on the bottom right of the dashboard!
