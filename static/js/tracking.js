const WS_BASE = `ws://${window.location.host}`;
const LOCATION_INTERVAL_MS = 5000; // broadcast GPS every 5 seconds


//  TRACKING CLIENT
const TrackingClient = (() => {
  let socket        = null;
  let watchId       = null;
  let gpsInterval   = null;
  let lastLat       = null;
  let lastLng       = null;
  let reconnectTimer = null;
  let reconnectDelay = 3000;
  let _ambulanceId  = null;
  let _requestId    = null;
  let _mode         = null; // 'driver' | 'user'
  let _onLocation   = null;
  let _onStatus     = null;

  function _buildUrl(ambulanceId) {
    return `${WS_BASE}/ws/tracking/${ambulanceId}/`;
  }

  function _connect(ambulanceId, mode, onLocation, onStatus) {
    _ambulanceId = ambulanceId;
    _mode        = mode;
    _onLocation  = onLocation;
    _onStatus    = onStatus;

    if (socket) { socket.close(); socket = null; }

    try {
      socket = new WebSocket(_buildUrl(ambulanceId));
    } catch(e) {
      console.warn('[TrackingClient] WebSocket connect error:', e);
      _scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      console.log(`[TrackingClient] Connected (${mode}) to ambulance ${ambulanceId}`);
      reconnectDelay = 3000; // reset backoff
      if (mode === 'driver') _startGPSBroadcast();
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'location_update' && _onLocation) {
          _onLocation(parseFloat(data.latitude), parseFloat(data.longitude), data.timestamp);
        } else if (data.type === 'status_update' && _onStatus) {
          _onStatus(data.status, data.request_id);
        }
      } catch(e) {
        console.warn('[TrackingClient] Bad message:', e);
      }
    };

    socket.onclose = (e) => {
      console.log('[TrackingClient] Disconnected. Reconnecting…');
      _stopGPSBroadcast();
      _scheduleReconnect();
    };

    socket.onerror = (e) => {
      console.warn('[TrackingClient] Error:', e);
    };
  }

  function _scheduleReconnect() {
    clearTimeout(reconnectTimer);
    if (!_ambulanceId || !_mode) return;
    reconnectTimer = setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 1.5, 30000); // exp backoff up to 30s
      _connect(_ambulanceId, _mode, _onLocation, _onStatus);
    }, reconnectDelay);
  }

  //Driver GPS Broadcasting 

  function _startGPSBroadcast() {
    if (!navigator.geolocation) {
      console.warn('[TrackingClient] Geolocation not supported.');
      return;
    }

    // Get initial position immediately
    navigator.geolocation.getCurrentPosition(_sendLocation, _gpsError, {
      enableHighAccuracy: true, timeout: 10000,
    });

    // Then broadcast every N seconds
    gpsInterval = setInterval(() => {
      navigator.geolocation.getCurrentPosition(_sendLocation, _gpsError, {
        enableHighAccuracy: true, timeout: 8000,
      });
    }, LOCATION_INTERVAL_MS);

    // Also keep a continuous watch
    watchId = navigator.geolocation.watchPosition(_sendLocation, _gpsError, {
      enableHighAccuracy: true,
      maximumAge: 3000,
    });
  }

  function _stopGPSBroadcast() {
    if (watchId !== null) {
      navigator.geolocation.clearWatch(watchId);
      watchId = null;
    }
    if (gpsInterval) {
      clearInterval(gpsInterval);
      gpsInterval = null;
    }
  }

  function _sendLocation(position) {
    const lat = position.coords.latitude;
    const lng = position.coords.longitude;

    // Only send if position changed meaningfully (≥ ~5m)
    if (lastLat && lastLng) {
      const d = Math.abs(lat - lastLat) + Math.abs(lng - lastLng);
      if (d < 0.00005) return;
    }
    lastLat = lat; lastLng = lng;

    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type:       'location',
        lat:        lat,
        lng:        lng,
        request_id: _requestId,
      }));
    }
  }

  function _gpsError(err) {
    console.warn('[TrackingClient] GPS error:', err.message);
  }

  // Status Push (driver → users)

  function pushStatusUpdate(status, requestId) {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({
        type:       'status_update',
        status:     status,
        request_id: requestId,
      }));
    }
  }

  // Ping (keep-alive) 

  setInterval(() => {
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify({ type: 'ping' }));
    }
  }, 25000); // every 25s

  // Public API

  return {
    /**
     * Connect as DRIVER — start broadcasting GPS.
     * @param {string|number} ambulanceId
     * @param {string|number} requestId
     * @param {function} onStatus — called when status update received
     */
    connectAsDriver(ambulanceId, requestId, onStatus) {
      _requestId = requestId;
      _connect(ambulanceId, 'driver', null, onStatus);
    },

    /**
     * Connect as USER — receive live GPS updates.
     * @param {string|number} ambulanceId
     * @param {function} onLocation(lat, lng, timestamp)
     * @param {function} onStatus(status, requestId)
     */
    connectAsUser(ambulanceId, onLocation, onStatus) {
      _connect(ambulanceId, 'user', onLocation, onStatus);
    },

    /** Push a status update from driver side. */
    pushStatus: pushStatusUpdate,

    /** Disconnect and stop all GPS broadcasting. */
    disconnect() {
      _ambulanceId = null;
      _mode        = null;
      _stopGPSBroadcast();
      clearTimeout(reconnectTimer);
      if (socket) { socket.close(); socket = null; }
    },

    get connected() {
      return socket && socket.readyState === WebSocket.OPEN;
    },
  };
})();

 
//  NOTIFICATION CLIENT (driver dashboard)
const NotificationClient = (() => {
  let socket        = null;
  let reconnectTimer = null;
  let reconnectDelay = 3000;
  let _driverId     = null;
  let _onRequest    = null;
  let _onCancel     = null;

  function _buildUrl(driverId) {
    return `${WS_BASE}/ws/notifications/${driverId}/`;
  }

  function _connect(driverId, onRequest, onCancel) {
    _driverId  = driverId;
    _onRequest = onRequest;
    _onCancel  = onCancel;

    if (socket) { socket.close(); socket = null; }

    try {
      socket = new WebSocket(_buildUrl(driverId));
    } catch(e) {
      console.warn('[NotificationClient] Connect error:', e);
      _scheduleReconnect();
      return;
    }

    socket.onopen = () => {
      console.log('[NotificationClient] Connected, driver:', driverId);
      reconnectDelay = 3000;
    };

    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'new_request' && _onRequest) _onRequest(data);
        if (data.type === 'request_cancelled' && _onCancel) _onCancel(data);
      } catch(e) { /* ignore */ }
    };

    socket.onclose = () => {
      console.log('[NotificationClient] Disconnected. Reconnecting…');
      _scheduleReconnect();
    };

    // Ping every 20s
    setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        socket.send(JSON.stringify({ type: 'ping' }));
      }
    }, 20000);
  }

  function _scheduleReconnect() {
    clearTimeout(reconnectTimer);
    if (!_driverId) return;
    reconnectTimer = setTimeout(() => {
      reconnectDelay = Math.min(reconnectDelay * 1.5, 30000);
      _connect(_driverId, _onRequest, _onCancel);
    }, reconnectDelay);
  }

  return {
    /**
     * Connect to the driver notification channel.
     * @param {string|number} driverId
     * @param {function} onNewRequest(data) — called when a new request arrives
     * @param {function} onCancelled(data) — called when user cancels
     */
    connect(driverId, onNewRequest, onCancelled) {
      _connect(driverId, onNewRequest, onCancelled);
    },

    disconnect() {
      _driverId = null;
      clearTimeout(reconnectTimer);
      if (socket) { socket.close(); socket = null; }
    },

    get connected() {
      return socket && socket.readyState === WebSocket.OPEN;
    },
  };
})();
