import time
import json
import random
import requests
import psutil
import socket
import asyncio

try:
    from winsdk.windows.devices.geolocation import Geolocator, GeolocationAccessStatus
    HAS_WINSDK = True
except ImportError:
    HAS_WINSDK = False

# Configuration
BASE_URL = "http://localhost:8000/api/v1"
USERNAME = "testuser"
PASSWORD = "testpass"
INTERVAL_SECONDS = 10

def get_battery_info():
    battery = psutil.sensors_battery()
    if battery:
        return {
            "level": int(battery.percent),
            "is_charging": battery.power_plugged
        }
    return {"level": 100, "is_charging": True}

async def get_real_location():
    if HAS_WINSDK:
        try:
            locator = Geolocator()
            # Request permission if needed
            access_status = await Geolocator.request_access_async()
            if access_status == GeolocationAccessStatus.ALLOWED:
                pos = await locator.get_geoposition_async()
                if pos and pos.coordinate:
                    return {
                        "latitude": round(pos.coordinate.latitude, 6),
                        "longitude": round(pos.coordinate.longitude, 6),
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                    }
            else:
                print("Windows Location Services access denied! Check Windows Settings.")
        except Exception as e:
            print(f"Error getting native Windows location: {e}")
            
    # Fallback to simulated location near Surampalem if real GPS fails
    print("Falling back to simulated coordinates...")
    return {
        "latitude": round(17.0837 + (random.uniform(-0.0001, 0.0001)), 6),
        "longitude": round(82.0540 + (random.uniform(-0.0001, 0.0001)), 6),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }

async def async_main():
    print("SentinelTrack Smart Background Service Started.")
    
    # 1. Login and get JWT Token
    print(f"Logging in as {USERNAME}...")
    try:
        auth_resp = requests.post(f"{BASE_URL}/auth/token/", json={"username": USERNAME, "password": PASSWORD})
        if auth_resp.status_code != 200:
            print("Failed to authenticate. Exiting.")
            return
            
        token = auth_resp.json()['access']
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    except Exception as e:
        print(f"Could not reach backend: {e}")
        return
    
    # 2. Register Device
    hostname = socket.gethostname()
    mac_address = ':'.join(['{:02x}'.format((random.getrandbits(8))) for _ in range(6)])
    
    devices_resp = requests.get(f"{BASE_URL}/devices/", headers=headers)
    devices = devices_resp.json()
    
    laptop_device = next((d for d in devices if d['name'] == hostname), None)
    
    if not laptop_device:
        print(f"Registering new device: {hostname}")
        reg_resp = requests.post(f"{BASE_URL}/devices/", json={"name": hostname, "mac_address": mac_address}, headers=headers)
        if reg_resp.status_code == 201:
            laptop_device = reg_resp.json()
        else:
            print("Failed to register device", reg_resp.text)
            return
            
    device_id = laptop_device['id']
    print(f"Registered/Found Device ID: {device_id}")
    
    # 3. Telemetry Loop
    print("Starting Telemetry Loop...")
    while True:
        loc = await get_real_location()
        payload = {
            "location": loc,
            "battery": get_battery_info()
        }
        
        try:
            response = requests.post(f"{BASE_URL}/devices/{device_id}/upload_telemetry/", json=payload, headers=headers)
            print(f"[{time.strftime('%H:%M:%S')}] Telemetry uploaded. Status: {response.status_code}")
        except Exception as e:
            print(f"[{time.strftime('%H:%M:%S')}] Failed to upload telemetry: {e}")
            
        await asyncio.sleep(INTERVAL_SECONDS)

def main():
    asyncio.run(async_main())

if __name__ == "__main__":
    main()
