// f:\CN Hackathon\frontend\src\app\explore\page.js
'use client';

import React, { useState, useEffect, useMemo, useRef } from 'react';
import Link from 'next/link';
import Script from 'next/script';
import { api } from '@/services/api';
import { 
  Filter, MapPin, X, ChevronRight, ThumbsUp, Compass, Target 
} from 'lucide-react';
import styles from './page.module.css';
import { useApp } from '@/context/AppContext';

export default function ExploreMapPage() {
  const { user } = useApp();
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [mapError, setMapError] = useState(null);
  
  // Map References
  const mapRef = useRef(null);
  const markersRef = useRef([]);
  const [leafletReady, setLeafletReady] = useState(false);
  const [mapLoaded, setMapLoaded] = useState(false);

  // Filters
  const [showDrawer, setShowDrawer] = useState(true);
  const [selectedIssue, setSelectedIssue] = useState(null);
  
  const [filterCategory, setFilterCategory] = useState({
    Infrastructure: true,
    Sanitation: true,
    'Public Safety': true
  });
  
  const [filterStatus, setFilterStatus] = useState({
    reported: true,
    in_progress: true,
    resolved: false
  });
  const [userLocation, setUserLocation] = useState(null);

  // Fetch user location for the marker
  useEffect(() => {
    if (typeof window !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setUserLocation({ lat: latitude, lng: longitude });
        },
        (err) => {
          console.warn('Could not get user geolocation for marker:', err);
        }
      );
    }
  }, []);

  // 1. Fetch Issues on mount
  useEffect(() => {
    async function loadIssues() {
      try {
        const list = await api.listIssues();
        setIssues(list.items || list || []);
      } catch (err) {
        console.error('Failed to load issues for map:', err);
        setIssues([]);
      } finally {
        setLoading(false);
      }
    }

    loadIssues();
  }, []);

  // 2. Check if Leaflet is already in the window on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && window.L) {
      setLeafletReady(true);
    }
  }, []);

  // 3. Initialize map once Leaflet is ready
  useEffect(() => {
    if (!leafletReady || typeof window === 'undefined' || !window.L || mapRef.current) return;

    const initMap = () => {
      try {
        const container = document.getElementById('leaflet-map-container');
        if (!container) {
          // If the DOM container isn't ready yet, retry in 100ms
          setTimeout(initMap, 100);
          return;
        }

        const L = window.L;
        // Create map instance
        const map = L.map('leaflet-map-container', {
          zoomControl: false
        });

        if (user?.region?.bbox) {
          const { south, north, west, east } = user.region.bbox;
          map.fitBounds([[south, west], [north, east]], { padding: [20, 20] });
        } else {
          map.setView([12.9716, 77.5946], 12); // Fallback to Bangalore
          if (typeof window !== 'undefined' && navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
              (position) => {
                const { latitude, longitude } = position.coords;
                map.setView([latitude, longitude], 12);
              },
              (err) => console.warn('Could not locate user:', err)
            );
          }
        }

        // Render boundary GeoJSON if available
        if (user?.region?.boundary_geojson) {
          L.geoJSON(user.region.boundary_geojson, {
            style: {
              color: '#2C6E8C',
              weight: 2,
              dashArray: '4 4',
              fillColor: '#2C6E8C',
              fillOpacity: 0.05
            }
          }).addTo(map);
        }

        // CARTO Voyager Tiles (modern, clean, fits premium blueprint/neon aesthetic)
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
          attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
          subdomains: 'abcd',
          maxZoom: 20
        }).addTo(map);

        // Add Zoom control at top-right
        L.control.zoom({
          position: 'topright'
        }).addTo(map);

        mapRef.current = map;
        setMapLoaded(true);
      } catch (err) {
        console.error('Error initializing map:', err);
        setMapError(err.message || String(err));
      }
    };

    initMap();

    return () => {
      if (mapRef.current) {
        mapRef.current.remove();
        mapRef.current = null;
        setMapLoaded(false);
      }
    };
  }, [leafletReady]);

  // Helper mappings between DB models and UI filters
  const getUIMapCategory = (dbCategory) => {
    const cat = dbCategory ? dbCategory.toLowerCase() : 'other';
    const categoryMapping = {
      pothole: 'Infrastructure',
      road_damage: 'Infrastructure',
      encroachment: 'Infrastructure',
      other: 'Infrastructure',
      garbage: 'Sanitation',
      drainage: 'Sanitation',
      water_leak: 'Sanitation',
      streetlight: 'Public Safety',
      noise: 'Public Safety',
      infrastructure: 'Infrastructure',
      sanitation: 'Sanitation',
      'public safety': 'Public Safety'
    };
    return categoryMapping[cat] || 'Infrastructure';
  };

  const getUIMapStatus = (dbStatus) => {
    if (dbStatus === 'resolved') return 'resolved';
    if (dbStatus === 'assigned' || dbStatus === 'in_progress') return 'in_progress';
    return 'reported'; // reported, flagged, duplicate
  };

  // Filter logic
  const filteredIssues = useMemo(() => {
    return issues.filter(issue => {
      const uiCategory = getUIMapCategory(issue.category);
      const uiStatus = getUIMapStatus(issue.status);
      if (!filterCategory[uiCategory]) return false;
      if (!filterStatus[uiStatus]) return false;
      return true;
    });
  }, [issues, filterCategory, filterStatus]);

  // 4. Render / Update Leaflet markers dynamically on the map
  useEffect(() => {
    if (!mapRef.current || !mapLoaded || typeof window === 'undefined' || !window.L) return;

    const L = window.L;
    const map = mapRef.current;

    // Clear old markers
    markersRef.current.forEach(m => map.removeLayer(m));
    markersRef.current = [];

    // Add user location marker
    if (userLocation) {
      const pulsingDotIcon = L.divIcon({
        className: 'user-location-marker',
        html: '<div class="pulse-ring"></div><div class="pulse-dot"></div>',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
      });

      const userMarker = L.marker([userLocation.lat, userLocation.lng], {
        icon: pulsingDotIcon,
        zIndexOffset: 1000
      })
      .bindPopup('<strong>You are here</strong>')
      .addTo(map);

      markersRef.current.push(userMarker);
    }

    // Add new markers
    filteredIssues.forEach(issue => {
      if (!issue.latitude || !issue.longitude) return;

      let markerColor = '#f59e0b'; // amber (assigned/in_progress)
      if (issue.status === 'resolved') {
        markerColor = '#10b981'; // green
      } else if (issue.severity === 'high' || issue.severity === 'critical') {
        markerColor = '#ef4444'; // red
      }

      // Styled custom marker HTML element
      const markerHtml = `
        <div class="custom-map-marker" style="
          position: relative;
          width: 16px; 
          height: 16px; 
          background-color: ${markerColor}; 
          border: 2.5px solid white; 
          border-radius: 50%;
          box-shadow: 0 2px 5px rgba(0,0,0,0.4);
          cursor: pointer;
        ">
          ${(issue.severity === 'high' && issue.status !== 'resolved') ? `
            <div style="
              position: absolute;
              top: -6px;
              left: -6px;
              width: 24px;
              height: 24px;
              border-radius: 50%;
              border: 2px solid ${markerColor};
              animation: markerPulseAnim 1.6s infinite ease-out;
              pointer-events: none;
            "></div>
          ` : ''}
        </div>
      `;

      const customIcon = L.divIcon({
        html: markerHtml,
        className: 'leaflet-custom-div-icon',
        iconSize: [16, 16],
        iconAnchor: [8, 8]
      });

      const marker = L.marker([issue.latitude, issue.longitude], { icon: customIcon })
        .addTo(map)
        .on('click', () => {
          setSelectedIssue(issue);
          map.setView([issue.latitude, issue.longitude], Math.max(map.getZoom(), 15));
        });

      markersRef.current.push(marker);
    });

    // Auto-fit map viewport bounds to wrap around all markers
    if (filteredIssues.length > 0) {
      const validPoints = filteredIssues
        .map(issue => {
          const lat = parseFloat(issue.latitude);
          const lng = parseFloat(issue.longitude);
          return [lat, lng];
        })
        .filter(([lat, lng]) => !isNaN(lat) && !isNaN(lng));
      
      if (validPoints.length > 0) {
        try {
          const bounds = L.latLngBounds(validPoints);
          if (bounds.isValid()) {
            map.fitBounds(bounds, { padding: [60, 60], maxZoom: 15 });
          }
        } catch (boundsErr) {
          console.warn('Invalid map bounds:', boundsErr);
        }
      }
    }
  }, [filteredIssues, mapLoaded, userLocation]);

  const handleToggleCategory = (cat) => {
    setFilterCategory(prev => ({ ...prev, [cat]: !prev[cat] }));
  };

  const handleToggleStatus = (stat) => {
    setFilterStatus(prev => ({ ...prev, [stat]: !prev[stat] }));
  };

  return (
    <div className={styles.exploreWrapper}>
      {/* React 19 stylesheet hoisting to head */}
      <link 
        rel="stylesheet" 
        href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"
        integrity="sha256-p4NxAoJBhIIN+hmNHrzRCf9tD/miZyoHS5obTRR9BMY="
        crossOrigin=""
      />
      
      {/* Dynamic Keyframes inject */}
      <style>{`
        @keyframes markerPulseAnim {
          0% { transform: scale(0.5); opacity: 0.8; }
          100% { transform: scale(1.8); opacity: 0; }
        }
        .leaflet-custom-div-icon {
          background: transparent !important;
          border: none !important;
        }
      `}</style>

      {/* Next.js Script manager loading leaflet.js */}
      <Script 
        src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"
        integrity="sha256-20nQCchB9co0qIjJZRGuk2/Z9VM+kNiyxNV1lvTlZBo="
        crossOrigin=""
        strategy="afterInteractive"
        onLoad={() => setLeafletReady(true)}
      />

      {/* Top Controls Banner */}
      <div className={styles.mapControlsHeader}>
        <Compass size={18} className={styles.compassIcon} />
        <span className="label-caps">CIVIC EXPLORER MAP</span>
        <span className="utility-code ml-auto">LIVE MAP UPDATES</span>
      </div>

      <div className={styles.mainCanvas}>
        
        {/* Left Drawer Filter Panel */}
        <aside className={`${styles.filterDrawer} ${showDrawer ? '' : styles.drawerHidden}`}>
          <div className={styles.drawerHeader}>
            <h3 className="label-caps">MAP FILTERS</h3>
            <button 
              className={styles.closeDrawerBtn} 
              onClick={() => setShowDrawer(!showDrawer)}
              title="Toggle drawer"
            >
              <Filter size={16} />
            </button>
          </div>
          
          <div className={styles.drawerBody}>
            {/* Category selection */}
            <div className={styles.filterSection}>
              <span className="label-caps text-secondary mb-2 block">CATEGORIES</span>
              <div className={styles.checkboxGroup}>
                {Object.keys(filterCategory).map(cat => (
                  <label key={cat} className={styles.checkboxLabel}>
                    <input 
                      type="checkbox" 
                      checked={filterCategory[cat]} 
                      onChange={() => handleToggleCategory(cat)}
                      className={styles.checkbox}
                    />
                    <span className="utility-code">{cat}</span>
                  </label>
                ))}
              </div>
            </div>

            {/* Status selection */}
            <div className={styles.filterSection}>
              <span className="label-caps text-secondary mb-2 block">STATUSES</span>
              <div className={styles.checkboxGroup}>
                {Object.keys(filterStatus).map(stat => (
                  <label key={stat} className={styles.checkboxLabel}>
                    <input 
                      type="checkbox" 
                      checked={filterStatus[stat]} 
                      onChange={() => handleToggleStatus(stat)}
                      className={styles.checkbox}
                    />
                    <span className="utility-code">{stat.replace('_', ' ').toUpperCase()}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>
        </aside>

        {/* Real Leaflet Map Container Wrapper */}
        <div className={styles.mapPattern} style={{ position: 'relative' }}>
          
          <div 
            id="leaflet-map-container" 
            style={{ 
              position: 'absolute', 
              top: 0, 
              bottom: 0, 
              left: 0, 
              right: 0, 
              zIndex: 10,
              backgroundColor: '#f4f4f5' 
            }}
          />

          {user?.region?.bbox && mapLoaded && (
            <button
              onClick={() => {
                if (mapRef.current && user?.region?.bbox) {
                  const { south, north, west, east } = user.region.bbox;
                  mapRef.current.fitBounds([[south, west], [north, east]], { padding: [20, 20] });
                }
              }}
              className="blueprint-btn blueprint-btn-secondary"
              style={{
                position: 'absolute',
                top: '20px',
                left: '20px',
                zIndex: 100,
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

          {loading && (
            <div className={styles.mapLoading} style={{ zIndex: 20 }}>
              <span className="utility-code">RETRIEVING MAP COORDINATES...</span>
            </div>
          )}

          {mapError && (
            <div 
              style={{ 
                position: 'absolute', 
                top: '20px', 
                left: '50%', 
                transform: 'translateX(-50%)', 
                backgroundColor: '#fee2e2', 
                border: '1px solid #f87171', 
                color: '#991b1b', 
                padding: '12px 24px', 
                borderRadius: '6px', 
                zIndex: 100,
                boxShadow: '0 4px 12px rgba(0,0,0,0.1)'
              }}
            >
              <strong>Map Initialization Failed:</strong> {mapError}
            </div>
          )}
        </div>

        {/* Right Details Panel Slide-over */}
        {selectedIssue && (
          <aside className={styles.detailsSlideOver}>
            <div className={styles.slideHeader}>
              <div className={styles.tagRow}>
                <span className={`${styles.statusBadge} ${
                  selectedIssue.status === 'resolved' ? styles.statusResolved : 
                  selectedIssue.status === 'in_progress' ? styles.statusProgress : styles.statusReported
                }`}>
                  {selectedIssue.status.replace('_', ' ').toUpperCase()}
                </span>
                <span className="utility-code text-outline">{selectedIssue.id.substring(0, 8)}</span>
              </div>
              <button className={styles.closeBtn} onClick={() => setSelectedIssue(null)}>
                <X size={16} />
              </button>
            </div>

            <div className={styles.slideBody}>
              <h3 className={styles.slideTitle}>{selectedIssue.title}</h3>
              <p className={styles.slideDesc}>{selectedIssue.description}</p>

              <div className={styles.slideMetaList}>
                <div className={styles.metaRow}>
                  <MapPin size={14} />
                  <span className="utility-code" style={{ fontSize: '11px' }}>
                    {selectedIssue.address || `Lat: ${selectedIssue.latitude?.toFixed(4)}, Lng: ${selectedIssue.longitude?.toFixed(4)}`}
                  </span>
                </div>
                <div className={styles.metaRow}>
                  <ThumbsUp size={14} />
                  <span className="utility-code">{selectedIssue.upvotes_count || 0} Upvotes</span>
                </div>
              </div>

              <Link 
                href={`/issues/${selectedIssue.id}`} 
                className={`${styles.viewDetailsBtn} blueprint-btn blueprint-btn-primary`}
              >
                <span>VIEW FULL DETAILS</span>
                <ChevronRight size={14} />
              </Link>
            </div>
          </aside>
        )}

      </div>
    </div>
  );
}
