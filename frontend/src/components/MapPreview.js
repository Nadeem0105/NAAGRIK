// f:\CN Hackathon\frontend\src\components\MapPreview.js
'use client';

import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import styles from '../app/page.module.css';

// SVG icons matching the Lucide designs for the map markers
const criticalSvg = `
  <div style="display: flex; flex-direction: column; align-items: center;">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#ef4444" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>
    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #ef4444; margin-top: 4px; border: 1px solid white;"></div>
  </div>
`;

const progressSvg = `
  <div style="display: flex; flex-direction: column; align-items: center;">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));"><path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/></svg>
    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #f59e0b; margin-top: 4px; border: 1px solid white;"></div>
  </div>
`;

const resolvedSvg = `
  <div style="display: flex; flex-direction: column; align-items: center;">
    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="filter: drop-shadow(0 2px 4px rgba(0,0,0,0.15));"><path d="M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10z"/><path d="m9 12 2 2 4-4"/></svg>
    <div style="width: 8px; height: 8px; border-radius: 50%; background-color: #10b981; margin-top: 4px; border: 1px solid white;"></div>
  </div>
`;

const getStatusIcon = (status) => {
  let html = criticalSvg;
  if (status === 'resolved') {
    html = resolvedSvg;
  } else if (status === 'in_progress' || status === 'assigned') {
    html = progressSvg;
  }

  return L.divIcon({
    html: html,
    className: '',
    iconSize: [24, 36],
    iconAnchor: [12, 36]
  });
};

// Component to dynamically update the map bounds or center when issues load
function ChangeView({ issues }) {
  const map = useMap();
  
  useEffect(() => {
    if (issues.length > 0) {
      const points = issues.map(i => [i.latitude, i.longitude]);
      if (points.length === 1) {
        map.setView(points[0], 13);
      } else {
        map.fitBounds(points, { padding: [40, 40], maxZoom: 14 });
      }
    }
  }, [issues, map]);

  return null;
}

export default function MapPreview({ issues = [] }) {
  const defaultCenter = [12.9716, 77.5946]; // Bengaluru default

  // Filter valid issues with coordinates
  const validIssues = issues.filter(
    (issue) => issue.latitude !== undefined && issue.longitude !== undefined && issue.latitude !== null && issue.longitude !== null
  );

  return (
    <MapContainer
      center={defaultCenter}
      zoom={12}
      zoomControl={false}
      dragging={false}
      scrollWheelZoom={false}
      doubleClickZoom={false}
      attributionControl={true}
      style={{ height: '100%', width: '100%', zIndex: 1 }}
    >
      <TileLayer
        url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
        attribution='&copy; <a href="https://carto.com/attributions">CARTO</a> &copy; <a href="https://openstreetmap.org/copyright">OpenStreetMap</a>'
        className={styles.npTiles}
      />
      <ChangeView issues={validIssues} />
      {validIssues.map((issue) => (
        <Marker
          key={issue.id}
          position={[issue.latitude, issue.longitude]}
          icon={getStatusIcon(issue.status)}
        />
      ))}
    </MapContainer>
  );
}
