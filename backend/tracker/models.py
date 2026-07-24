from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid

class User(AbstractUser):
    pass

class Device(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    name = models.CharField(max_length=255)
    mac_address = models.CharField(max_length=17, unique=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.mac_address})"

class Location(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='locations')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    altitude = models.FloatField(null=True, blank=True)
    speed = models.FloatField(null=True, blank=True)
    heading = models.FloatField(null=True, blank=True)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

class Battery(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='battery_logs')
    level = models.IntegerField() # 0 to 100
    voltage = models.FloatField(null=True, blank=True)
    is_charging = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

class Alert(models.Model):
    ALERT_TYPES = (
        ('MOTION', 'Motion Detected'),
        ('GEOFENCE_ENTER', 'Geofence Entered'),
        ('GEOFENCE_EXIT', 'Geofence Exited'),
        ('BATTERY_LOW', 'Battery Low'),
        ('OFFLINE', 'Device Offline'),
        ('TAMPER', 'Tamper Detected'),
    )
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='alerts')
    alert_type = models.CharField(max_length=20, choices=ALERT_TYPES)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

class Geofence(models.Model):
    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name='geofences')
    name = models.CharField(max_length=255)
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    radius = models.FloatField(help_text="Radius in meters")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.device.name})"
