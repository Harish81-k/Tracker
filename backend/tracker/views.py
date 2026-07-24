from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Device, Location, Battery, Alert, Geofence
from .serializers import (
    DeviceSerializer, LocationSerializer, BatterySerializer,
    AlertSerializer, GeofenceSerializer
)

class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Device.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def upload_telemetry(self, request, pk=None):
        device = self.get_object()
        
        location_data = request.data.get('location')
        battery_data = request.data.get('battery')
        
        if location_data:
            location_data['device'] = device.id
            loc_serializer = LocationSerializer(data=location_data)
            if loc_serializer.is_valid():
                loc_serializer.save()
            else:
                print("TELEMETRY LOC ERROR:", loc_serializer.errors)
                return Response(loc_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        if battery_data:
            battery_data['device'] = device.id
            bat_serializer = BatterySerializer(data=battery_data)
            if bat_serializer.is_valid():
                bat_serializer.save()
            else:
                return Response(bat_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                
        # Trigger Celery Task for Geofence & AI Verification
        from .tasks import process_telemetry
        process_telemetry.delay(
            device.id,
            loc_serializer.instance.id if location_data else None,
            bat_serializer.instance.id if battery_data else None
        )
                
        return Response({'status': 'telemetry recorded'})

    @action(detail=True, methods=['get'])
    def check_ota(self, request, pk=None):
        """Stub for Over-The-Air firmware updates"""
        device = self.get_object()
        # In a real app, query Firmware model to see if version > device.current_version
        return Response({
            'update_available': False,
            'latest_version': '1.0.0',
            'firmware_url': None
        })

class LocationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Location.objects.filter(device__owner=self.request.user)

class BatteryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BatterySerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Battery.objects.filter(device__owner=self.request.user)

class AlertViewSet(viewsets.ModelViewSet):
    serializer_class = AlertSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Alert.objects.filter(device__owner=self.request.user)

class GeofenceViewSet(viewsets.ModelViewSet):
    serializer_class = GeofenceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Geofence.objects.filter(device__owner=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("GEOFENCE VALIDATION ERROR:", serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
