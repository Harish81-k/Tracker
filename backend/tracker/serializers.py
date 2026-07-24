from rest_framework import serializers
from .models import Device, Location, Battery, Alert, Geofence, User

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'

class BatterySerializer(serializers.ModelSerializer):
    class Meta:
        model = Battery
        fields = '__all__'

class DeviceSerializer(serializers.ModelSerializer):
    latest_location = serializers.SerializerMethodField()
    latest_battery = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = ['id', 'name', 'mac_address', 'is_active', 'created_at', 'latest_location', 'latest_battery']
        read_only_fields = ['owner']

    def get_latest_location(self, obj):
        loc = obj.locations.order_by('-timestamp').first()
        if loc:
            return LocationSerializer(loc).data
        return None

    def get_latest_battery(self, obj):
        bat = obj.battery_logs.order_by('-timestamp').first()
        if bat:
            return BatterySerializer(bat).data
        return None

class AlertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alert
        fields = '__all__'

class GeofenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Geofence
        fields = '__all__'
