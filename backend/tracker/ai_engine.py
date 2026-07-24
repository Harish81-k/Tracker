import statistics
from datetime import timedelta
from django.utils import timezone

def detect_unusual_movement(location, recent_locations):
    """
    Simple AI Heuristic using standard deviation of speed.
    If current speed > mean + 2*std_dev of historical speeds, flag it.
    """
    if not recent_locations or len(recent_locations) < 5:
        return False
        
    speeds = [float(loc.speed) for loc in recent_locations if loc.speed is not None]
    if not speeds or location.speed is None:
        return False
        
    mean_speed = statistics.mean(speeds)
    std_speed = statistics.stdev(speeds) if len(speeds) > 1 else 0.0
    
    # If speed is exceptionally high compared to historical data
    if float(location.speed) > (mean_speed + 2 * std_speed) and float(location.speed) > 20.0:
        return True
    return False

def predict_battery_depletion(battery_logs):
    """
    Linear regression heuristic to predict time until battery hits 0%.
    Returns expected hours remaining.
    """
    if not battery_logs or len(battery_logs) < 2:
        return None
        
    # Only look at the discharging phase
    if battery_logs[0].is_charging:
        return None
        
    # Calculate average drain per hour over the last few logs
    first = battery_logs[-1]
    last = battery_logs[0]
    
    time_diff_hours = (last.timestamp - first.timestamp).total_seconds() / 3600.0
    if time_diff_hours <= 0:
        return None
        
    drain = first.level - last.level
    if drain <= 0:
        return None # Battery went up or didn't change
        
    drain_rate_per_hour = drain / time_diff_hours
    hours_remaining = last.level / drain_rate_per_hour
    
    return round(hours_remaining, 1)
