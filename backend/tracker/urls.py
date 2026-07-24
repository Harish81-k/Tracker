from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DeviceViewSet, LocationViewSet, BatteryViewSet, AlertViewSet, GeofenceViewSet

router = DefaultRouter()
router.register(r'devices', DeviceViewSet, basename='device')
router.register(r'locations', LocationViewSet, basename='location')
router.register(r'battery', BatteryViewSet, basename='battery')
router.register(r'alerts', AlertViewSet, basename='alert')
router.register(r'geofences', GeofenceViewSet, basename='geofence')

urlpatterns = [
    path('', include(router.urls)),
]
