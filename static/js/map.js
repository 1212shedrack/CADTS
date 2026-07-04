// Map Initialization
let map, userMarker, userCircle;
let ambulanceMarkers = {};
let hospitalMarkers  = [];
let routeLayer       = null;
let selectedAmbulance = null;
let watchId = null;

function initMap(centerLat = -6.7924, centerLng = 39.2083) {
  map = L.map('map', {
    center: [centerLat, centerLng],
    zoom: 13,
    zoomControl: false,
    dragging: !L.Browser.mobile // Fixes page scroll issue on mobile
  });

  // OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
    maxZoom: 19,
  }).addTo(map);

  // Custom zoom control position
  L.control.zoom({ position: 'bottomright' }).addTo(map);

  return map;
}

//Custom Marker Icons
const icons = {
  user: L.divIcon({
    className: '',
    html: `<div style="
      width:20px; height:20px;
      background:#3b82f6;
      border:3px solid #fff;
      border-radius:50%;
      box-shadow:0 0 0 4px rgba(59,130,246,0.3), 0 2px 8px rgba(0,0,0,0.4);
    "></div>`,
    iconSize:   [20, 20],
    iconAnchor: [10, 10],
  }),

  ambulanceAvailable: L.divIcon({
    className: '',
    html: `<div style="
      background:linear-gradient(135deg,#10b981,#059669);
      border:2px solid #fff;
      border-radius:50%;
      width:36px; height:36px;
      display:flex; align-items:center; justify-content:center;
      font-size:18px;
      box-shadow:0 0 0 3px rgba(16,185,129,0.3), 0 4px 12px rgba(0,0,0,0.4);
      cursor:pointer;
    ">🚑</div>`,
    iconSize:   [36, 36],
    iconAnchor: [18, 18],
    popupAnchor:[0, -20],
  }),

  ambulanceBusy: L.divIcon({
    className: '',
    html: `<div style="
      background:linear-gradient(135deg,#ef4444,#dc2626);
      border:2px solid #fff;
      border-radius:50%;
      width:36px; height:36px;
      display:flex; align-items:center; justify-content:center;
      font-size:18px;
      box-shadow:0 0 0 3px rgba(239,68,68,0.3), 0 4px 12px rgba(0,0,0,0.4);
    ">🚑</div>`,
    iconSize:   [36, 36],
    iconAnchor: [18, 18],
    popupAnchor:[0, -20],
  }),

  hospital: L.divIcon({
    className: '',
    html: `<div style="
      background:linear-gradient(135deg,#e63946,#c1121f);
      border:2px solid #fff;
      border-radius:8px;
      width:32px; height:32px;
      display:flex; align-items:center; justify-content:center;
      font-size:16px;
      box-shadow:0 4px 12px rgba(0,0,0,0.4);
      cursor:pointer;
    ">🏥</div>`,
    iconSize:   [32, 32],
    iconAnchor: [16, 16],
    popupAnchor:[0, -18],
  }),
};

// User Location
function locateUser(callback) {
  if (!navigator.geolocation) {
    alert('Geolocation is not supported by your browser.');
    return;
  }

  navigator.geolocation.getCurrentPosition(
    (pos) => {
      const lat = pos.coords.latitude;
      const lng = pos.coords.longitude;
      placeUserMarker(lat, lng);
      map.setView([lat, lng], 14);
      if (callback) callback(lat, lng);
    },
    (err) => {
      console.warn('Geolocation error:', err.message);
      // Default to Dar es Salaam centre
      if (callback) callback(-6.7924, 39.2083);
    },
    { enableHighAccuracy: true, timeout: 10000 }
  );
}

function placeUserMarker(lat, lng) {
  if (userMarker)  map.removeLayer(userMarker);
  if (userCircle)  map.removeLayer(userCircle);

  userMarker = L.marker([lat, lng], { icon: icons.user })
    .addTo(map)
    .bindPopup('<strong>📍 Your Location</strong>');

  userCircle = L.circle([lat, lng], {
    radius: 200,
    color: '#3b82f6',
    fillColor: '#3b82f6',
    fillOpacity: 0.08,
    weight: 1,
  }).addTo(map);
}

function watchUserLocation() {
  if (!navigator.geolocation) return;
  watchId = navigator.geolocation.watchPosition(
    (pos) => placeUserMarker(pos.coords.latitude, pos.coords.longitude),
    () => {},
    { enableHighAccuracy: true }
  );
}

function stopWatchingLocation() {
  if (watchId !== null) {
    navigator.geolocation.clearWatch(watchId);
    watchId = null;
  }
}

// Ambulance Markers
async function loadAmbulances(onSelectCallback) {
  try {
    const res = await API.request('/api/ambulances/');
    if (!res?.ok) return;
    const ambulances = await res.json();

    // Remove old markers
    Object.values(ambulanceMarkers).forEach(m => map.removeLayer(m));
    ambulanceMarkers = {};

    ambulances.forEach(amb => {
      if (!amb.latitude || !amb.longitude) return;

      const icon   = amb.status === 'available' ? icons.ambulanceAvailable : icons.ambulanceBusy;
      const marker = L.marker([parseFloat(amb.latitude), parseFloat(amb.longitude)], { icon })
        .addTo(map);

      const popupHtml = `
        <div style="min-width:200px;font-family:'Inter',sans-serif;">
          <div style="font-weight:700;font-size:1rem;margin-bottom:4px;">🚑 ${amb.ambulance_name}</div>
          <div style="font-size:0.82rem;color:#6b7280;margin-bottom:8px;">Plate: ${amb.plate_number}</div>
          <div style="font-size:0.82rem;margin-bottom:4px;">Driver: <strong>${amb.driver_name || 'Unassigned'}</strong></div>
          <div style="margin-bottom:12px;">
            <span style="
              display:inline-block;padding:2px 10px;border-radius:999px;font-size:0.75rem;font-weight:600;
              background:${amb.status==='available'?'rgba(16,185,129,0.15)':'rgba(239,68,68,0.15)'};
              color:${amb.status==='available'?'#34d399':'#f87171'};">
              ● ${amb.status}
            </span>
          </div>
          ${amb.status === 'available' ? `
            <button onclick="window.selectAmbulance(${amb.id},'${amb.ambulance_name}')"
              style="width:100%;padding:8px;background:linear-gradient(135deg,#e63946,#c1121f);
                     color:#fff;border:none;border-radius:6px;font-weight:600;
                     cursor:pointer;font-size:0.85rem;">
              Request This Ambulance
            </button>` : `
            <p style="color:#f87171;font-size:0.82rem;text-align:center;margin:0;">Currently busy</p>`}
        </div>`;

      marker.bindPopup(popupHtml, { maxWidth: 260 });

      if (amb.status === 'available' && onSelectCallback) {
        marker.on('click', () => {
          selectedAmbulance = amb;
        });
      }

      ambulanceMarkers[amb.id] = marker;
    });

    return ambulances;
  } catch(e) {
    console.error('Failed to load ambulances:', e);
    return [];
  }
}

// Hospital Markers (Overpass API)
async function loadHospitals(lat, lng, radius = 5000) {
  // Clear old markers
  hospitalMarkers.forEach(m => map.removeLayer(m));
  hospitalMarkers = [];

  const query = `
    [out:json][timeout:25];
    (
      node["amenity"="hospital"](around:${radius},${lat},${lng});
      way["amenity"="hospital"](around:${radius},${lat},${lng});
      node["amenity"="clinic"](around:${radius},${lat},${lng});
    );
    out center;
  `;

  try {
    const res = await fetch('https://overpass-api.de/api/interpreter', {
      method: 'POST',
      body: query,
    });
    if (!res.ok) return [];
    const data = await res.json();
    const hospitals = [];

    data.elements.forEach(el => {
      const elLat  = el.lat  ?? el.center?.lat;
      const elLng  = el.lon  ?? el.center?.lon;
      const name   = el.tags?.name || 'Hospital';
      const type   = el.tags?.amenity || 'hospital';
      if (!elLat || !elLng) return;

      const marker = L.marker([elLat, elLng], { icon: icons.hospital })
        .addTo(map)
        .bindPopup(`
          <div style="min-width:180px;font-family:'Inter',sans-serif;">
            <div style="font-weight:700;margin-bottom:4px;">🏥 ${name}</div>
            <div style="font-size:0.8rem;color:#6b7280;text-transform:capitalize;">${type}</div>
            ${el.tags?.phone ? `<div style="font-size:0.8rem;margin-top:4px;">📞 ${el.tags.phone}</div>` : ''}
          </div>
        `, { maxWidth: 240 });

      hospitalMarkers.push(marker);
      hospitals.push({ name, lat: elLat, lng: elLng, type });
    });

    return hospitals;
  } catch(e) {
    console.error('Overpass API error:', e);
    return [];
  }
}

// OSRM Routing
async function drawRoute(fromLat, fromLng, toLat, toLng) {
  clearRoute();

  const url = `https://router.project-osrm.org/route/v1/driving/${fromLng},${fromLat};${toLng},${toLat}?overview=full&geometries=geojson`;

  try {
    const res  = await fetch(url);
    const data = await res.json();

    if (data.code !== 'Ok' || !data.routes.length) return null;

    const route     = data.routes[0];
    const coords    = route.geometry.coordinates.map(([lng, lat]) => [lat, lng]);
    const distanceKm = (route.distance / 1000).toFixed(2);
    const durationMin = Math.ceil(route.duration / 60);

    routeLayer = L.polyline(coords, {
      color:     '#e63946',
      weight:    5,
      opacity:   0.85,
      dashArray: null,
    }).addTo(map);

    // Fit map to route bounds
    map.fitBounds(routeLayer.getBounds(), { padding: [60, 60] });

    return { distanceKm, durationMin };
  } catch(e) {
    console.error('OSRM routing error:', e);
    return null;
  }
}

function clearRoute() {
  if (routeLayer) {
    map.removeLayer(routeLayer);
    routeLayer = null;
  }
}

// Update Single Ambulance Marker (for live tracking)
function updateAmbulanceMarker(ambulanceId, lat, lng) {
  const marker = ambulanceMarkers[ambulanceId];
  if (marker) {
    marker.setLatLng([lat, lng]);
  }
}

// Global handler for popup request button
window.selectAmbulance = function(id, name) {
  selectedAmbulance = { id, ambulance_name: name };
  if (typeof onAmbulanceSelected === 'function') {
    onAmbulanceSelected(id, name);
  }
};
