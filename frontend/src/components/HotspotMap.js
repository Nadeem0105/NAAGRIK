// f:\CN Hackathon\frontend\src\components\HotspotMap.js
'use client';

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { MapContainer, TileLayer, Circle, Popup, useMap, GeoJSON } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import styles from '../app/page.module.css';
import { useApp } from '@/context/AppContext';
import { Target } from 'lucide-react';

// Sub-component to handle map view adjustments and boundary rendering
function AdminMapController({ user, hotspots, recenterCount }) {
  const map = useMap();
  const hasFittedRef = useRef(false);

  const fitToRegion = useCallback(() => {
    if (user?.region?.bbox) {
      const { south, north, west, east } = user.region.bbox;
      map.fitBounds([[south, west], [north, east]], { padding: [20, 20] });
    }
  }, [user, map]);

  // Fit on initial load
  useEffect(() => {
    if (user?.region?.bbox && !hasFittedRef.current) {
      fitToRegion();
      hasFittedRef.current = true;
    } else if (hotspots.length > 0 && !user?.region?.bbox && !hasFittedRef.current) {
      const points = hotspots.map(h => [h.latitude, h.longitude]);
      if (points.length === 1) {
        map.setView(points[0], 13);
      } else {
        map.fitBounds(points, { padding: [40, 40], maxZoom: 14 });
      }
      hasFittedRef.current = true;
    }
  }, [user, hotspots, map, fitToRegion]);

  // Fit on manual recenter trigger
  useEffect(() => {
    if (recenterCount > 0) {
      fitToRegion();
    }
  }, [recenterCount, fitToRegion]);

  return (
    <>
      {user?.region?.boundary_geojson && (
        <GeoJSON
          key={user.region.id}
          data={user.region.boundary_geojson}
          style={{
            color: '#2C6E8C',
            weight: 2,
            dashArray: '4 4',
            fillColor: '#2C6E8C',
            fillOpacity: 0.05
          }}
        />
      )}
    </>
  );
}

export default function HotspotMap({ hotspots = [] }) {
  const { user } = useApp();
  const [recenterCount, setRecenterCount] = useState(0);
  const defaultCenter = [13.0827, 80.2707]; // Chennai default

  // Clean Leaflet marker icons default issues
  useEffect(() => {
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
      iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
      shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
    });
  }, []);

  const handleRecenter = () => {
    setRecenterCount(prev => prev + 1);
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%' }}>
      <MapContainer
        center={defaultCenter}
        zoom={12}
        style={{ height: '100%', width: '100%', zIndex: 1 }}
      >
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
          className={styles.npTiles}
        />
        <AdminMapController user={user} hotspots={hotspots} recenterCount={recenterCount} />
        {hotspots.map((hotspot, idx) => (
          <Circle
            key={idx}
            center={[hotspot.latitude, hotspot.longitude]}
            radius={hotspot.radius_meters || 200}
            pathOptions={{
              color: '#ef4444',
              fillColor: '#ef4444',
              fillOpacity: 0.35,
              weight: 2
            }}
          >
            <Popup>
              <div style={{ fontFamily: 'var(--font-body)', fontSize: '13px', padding: '4px' }}>
                <div style={{ fontWeight: 'bold', textTransform: 'uppercase', color: '#ef4444', marginBottom: '4px' }}>
                  🔥 Hotspot Detected
                </div>
                <div style={{ marginBottom: '2px' }}>
                  <strong>Top Category:</strong> {hotspot.top_category}
                </div>
                <div style={{ marginBottom: '2px' }}>
                  <strong>Active Reports:</strong> {hotspot.issue_count}
                </div>
                <div>
                  <strong>Radius:</strong> {Math.round(hotspot.radius_meters)}m
                </div>
              </div>
            </Popup>
          </Circle>
        ))}
      </MapContainer>

      {/* Recenter Button */}
      {user?.region?.bbox && (
        <button
          onClick={handleRecenter}
          className="blueprint-btn blueprint-btn-secondary"
          style={{
            position: 'absolute',
            top: '12px',
            left: '12px',
            zIndex: 1000,
            padding: '8px 12px',
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            backgroundColor: 'var(--paper-bright)'
          }}
          title="Recenter to Jurisdiction"
        >
          <Target size={14} />
          <span style={{ fontSize: '11px', fontWeight: 'bold' }}>RECENTER</span>
        </button>
      )}
    </div>
  );
}
