import math
from celery import shared_task
from .models import Device, Location, Geofence, Alert, Battery
from .ai_engine import detect_unusual_movement, predict_battery_depletion

def haversine(lat1, lon1, lat2, lon2):
    """Calculate distance in meters between two lat/lon points."""
    R = 6371000 # Earth radius in meters
    phi1, phi2 = math.radians(float(lat1)), math.radians(float(lat2))
    delta_phi = math.radians(float(lat2) - float(lat1))
    delta_lambda = math.radians(float(lon2) - float(lon1))
    
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

@shared_task
def process_telemetry(device_id, location_id=None, battery_id=None):
    device = Device.objects.get(id=device_id)
    
    if location_id:
        location = Location.objects.get(id=location_id)
        # 1. Geofence Check
        geofences = Geofence.objects.filter(device=device, is_active=True)
        for gf in geofences:
            dist = haversine(location.latitude, location.longitude, gf.latitude, gf.longitude)
            if dist > gf.radius:
                Alert.objects.create(
                    device=device,
                    alert_type='GEOFENCE_EXIT',
                    message=f'Device left geofence {gf.name}. Distance: {int(dist)}m'
                )

        # 2. AI Movement Check
        recent_locs = Location.objects.filter(device=device).exclude(id=location_id).order_by('-timestamp')[:10]
        if detect_unusual_movement(location, list(recent_locs)):
            Alert.objects.create(
                device=device,
                alert_type='MOTION',
                message='Unusual movement pattern detected by AI Engine.'
            )
            
    if battery_id:
        # 3. AI Battery Prediction
        recent_bats = list(Battery.objects.filter(device=device).order_by('-timestamp')[:5])
        hours_left = predict_battery_depletion(recent_bats)
        
        current_bat = recent_bats[0]
        if current_bat.level <= 15:
            Alert.objects.create(
                device=device,
                alert_type='BATTERY_LOW',
                message=f'Battery critical ({current_bat.level}%). Est. time remaining: {hours_left} hrs.'
            )
