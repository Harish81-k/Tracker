import { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMapEvents, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import './App.css';

// Fix for default marker icons in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
});

interface Device {
  id: string;
  name: string;
  mac_address: string;
  is_active: boolean;
  latest_location?: {
    latitude: number;
    longitude: number;
    speed?: number;
    timestamp: string;
  };
  latest_battery?: {
    level: number;
    is_charging: boolean;
  };
  status: 'online' | 'offline';
}

interface Alert {
  id: number;
  alert_type: string;
  message: string;
  created_at: string;
  device: string;
}

interface Geofence {
  id: number;
  name: string;
  latitude: string | number;
  longitude: string | number;
  radius: number;
  is_active: boolean;
  device: string;
}

// Component to handle map clicks for adding geofences
function MapClickEvents({ onMapClick }: { onMapClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click(e) {
      onMapClick(e.latlng.lat, e.latlng.lng);
    }
  });
  return null;
}

// Component to recenter the map dynamically when the center state changes
function RecenterMap({ center }: { center: [number, number] }) {
  const map = useMap();
  useEffect(() => {
    map.setView(center, map.getZoom());
  }, [center, map]);
  return null;
}

// Component to dynamically fetch and display address based on coordinates
function AddressLabel({ lat, lng }: { lat: number, lng: number }) {
  const [address, setAddress] = useState<string>('Loading address...');
  
  useEffect(() => {
    setAddress('Loading address...');
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 3000);

    fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${lat}&lon=${lng}`, { signal: controller.signal })
      .then(res => res.json())
      .then(data => {
        clearTimeout(timeoutId);
        setAddress(data.display_name || 'Address not found');
      })
      .catch(() => {
        clearTimeout(timeoutId);
        setAddress(`Lat: ${Number(lat).toFixed(5)}, Lng: ${Number(lng).toFixed(5)} (Offline)`);
      });

    return () => {
      clearTimeout(timeoutId);
      controller.abort();
    };
  }, [lat, lng]);
  
  return <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>{address}</span>;
}

function App() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [geofences, setGeofences] = useState<Geofence[]>([]);
  
  const [token, setToken] = useState<string | null>(null);
  const [isAddingGeofence, setIsAddingGeofence] = useState(false);
  const [mapCenter, setMapCenter] = useState<[number, number]>([20.5937, 78.9629]); // Default India

  useEffect(() => {
    // Attempt to get user's real location for the map center
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition((position) => {
        setMapCenter([position.coords.latitude, position.coords.longitude]);
      });
    }
  }, []);

  // Authenticate (Test User)
  useEffect(() => {
    let API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    if (!API_URL.endsWith('/api/v1') && !API_URL.endsWith('/api/v1/')) {
        API_URL = API_URL.replace(/\/$/, '') + '/api/v1';
    }

    fetch(`${API_URL}/auth/token/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: 'testuser', password: 'testpass' })
    })
    .then(res => res.json())
    .then(data => setToken(data.access))
    .catch(console.error);
  }, []);

  // Fetch Data
  useEffect(() => {
    if (!token) return;

    let API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
    if (!API_URL.endsWith('/api/v1') && !API_URL.endsWith('/api/v1/')) {
        API_URL = API_URL.replace(/\/$/, '') + '/api/v1';
    }

    const fetchData = async () => {
      try {
        // Fetch Devices
        const devRes = await fetch(`${API_URL}/devices/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const devicesData = await devRes.json();
        const enrichedDevices = devicesData.map((d: any) => ({
          ...d,
          status: d.is_active ? 'online' : 'offline',
        }));
        setDevices(enrichedDevices);

        // Fetch Alerts
        const alertsRes = await fetch(`${API_URL}/alerts/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const alertsData = await alertsRes.json();
        setAlerts(alertsData);

        // Fetch Geofences
        const geoRes = await fetch(`${API_URL}/geofences/`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        const geoData = await geoRes.json();
        setGeofences(geoData);
        
      } catch (e) {
        console.error(e);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, [token]);

  const handleMapClick = async (lat: number, lng: number) => {
    if (!isAddingGeofence || !token || devices.length === 0) return;
    
    // Auto-assign to the first device for simplicity in MVP
    const targetDevice = devices[0];
    
    const payload = {
      name: `Geofence - ${new Date().toLocaleTimeString()}`,
      latitude: lat.toFixed(6),
      longitude: lng.toFixed(6),
      radius: 500, // 500 meters
      device: targetDevice.id,
      is_active: true
    };
    
    try {
      const res = await fetch('http://localhost:8000/api/v1/geofences/', {
        method: 'POST',
        headers: { 
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}` 
        },
        body: JSON.stringify(payload)
      });
      if (res.ok) {
        const newGeo = await res.json();
        setGeofences(prev => [...prev, newGeo]);
        setIsAddingGeofence(false);
      } else {
        const errorText = await res.text();
        console.error("Geofence creation failed:", res.status, errorText);
        alert(`Failed to add Geofence (Status ${res.status}):\n${errorText}`);
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"></div>
          <div className="brand-title">SentinelTrack</div>
        </div>
        
        <nav className="nav-menu">
          <div className="nav-item active">
            <span>Live Map</span>
          </div>
          <div className="nav-item">
            <span>Devices</span>
          </div>
          <div 
            className={`nav-item ${isAddingGeofence ? 'active-draw' : ''}`}
            onClick={() => setIsAddingGeofence(!isAddingGeofence)}
            style={{ cursor: 'pointer', border: isAddingGeofence ? '1px solid var(--accent)' : 'none' }}
          >
            <span>{isAddingGeofence ? 'Cancel Drawing...' : '+ Add Geofence'}</span>
          </div>
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className="main-content">
        
        <div className="map-container" style={{ cursor: isAddingGeofence ? 'crosshair' : 'default' }}>
          <MapContainer center={mapCenter} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
              attribution='Tiles &copy; Esri &mdash; Source: Esri, i-cubed, USDA, USGS, AEX, GeoEye, Getmapping, Aerogrid, IGN, IGP, UPR-EGP, and the GIS User Community'
            />
            <RecenterMap center={mapCenter} />
            
            <MapClickEvents onMapClick={handleMapClick} />

            {/* Render Devices */}
            {devices.map(device => {
              if (device.latest_location) {
                return (
                  <Marker 
                    key={`dev-${device.id}`} 
                    position={[device.latest_location.latitude, device.latest_location.longitude]}
                  >
                    <Popup>
                      <strong>{device.name}</strong><br />
                      Status: {device.status}<br />
                      Battery: {device.latest_battery ? `${device.latest_battery.level}%` : 'N/A'}<br />
                      Updated: {new Date(device.latest_location.timestamp).toLocaleTimeString()}<br />
                      Address: <AddressLabel lat={device.latest_location.latitude} lng={device.latest_location.longitude} />
                    </Popup>
                  </Marker>
                )
              }
              return null;
            })}

            {/* Render Geofences */}
            {geofences.map(geo => (
              <Circle
                key={`geo-${geo.id}`}
                center={[Number(geo.latitude), Number(geo.longitude)]}
                radius={geo.radius}
                pathOptions={{ color: 'var(--accent)', fillColor: 'var(--accent)', fillOpacity: 0.2 }}
              >
                <Popup>{geo.name}</Popup>
              </Circle>
            ))}
          </MapContainer>
        </div>

        {/* Floating Right Panel (Devices & Alerts) */}
        <div className="right-panel">
          
          <div className="glass-panel" style={{ marginBottom: '20px' }}>
            <div className="panel-header">
              <h2 className="panel-title">Active Trackers</h2>
              <span className="badge">{devices.length}</span>
            </div>
            
            <div className="device-list">
              {devices.map(device => (
                <div key={device.id} className="device-card">
                  <div className="device-header">
                    <span className="device-name">{device.name}</span>
                    <div className={`status-dot ${device.status}`}></div>
                  </div>
                  <div className="device-info">
                    <div className="info-row">
                      <span>Battery</span>
                      <span style={{ color: device.latest_battery && device.latest_battery.level > 20 ? 'var(--success)' : 'var(--danger)' }}>
                        {device.latest_battery ? `${device.latest_battery.level}%` : 'N/A'}
                      </span>
                    </div>
                    {device.latest_location && (
                      <div className="info-row" style={{ marginTop: '5px' }}>
                        <span style={{ minWidth: '50px' }}>Location</span>
                        <AddressLabel lat={device.latest_location.latitude} lng={device.latest_location.longitude} />
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="glass-panel alerts-panel">
            <div className="panel-header">
              <h2 className="panel-title" style={{ color: 'var(--danger)' }}>System Alerts</h2>
              <span className="badge" style={{ backgroundColor: 'rgba(239, 68, 68, 0.2)', color: 'var(--danger)', borderColor: 'var(--danger)' }}>
                {alerts.length}
              </span>
            </div>
            
            <div className="alerts-list">
              {alerts.length === 0 ? (
                <div style={{ color: 'var(--text-muted)', textAlign: 'center', marginTop: 10 }}>No recent alerts</div>
              ) : (
                alerts.slice(0, 5).map(alert => (
                  <div key={alert.id} className="alert-item">
                    <div className="alert-header">
                      <span style={{ fontWeight: 'bold', fontSize: '0.85rem' }}>{alert.alert_type}</span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                        {new Date(alert.created_at).toLocaleTimeString()}
                      </span>
                    </div>
                    <div style={{ fontSize: '0.85rem', marginTop: 4 }}>{alert.message}</div>
                  </div>
                ))
              )}
            </div>
          </div>

        </div>
      </main>
    </div>
  );
}

export default App;
