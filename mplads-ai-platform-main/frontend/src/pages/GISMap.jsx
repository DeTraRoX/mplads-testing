import React, { useEffect, useState, useRef } from 'react';
import { useOutletContext, useNavigate } from 'react-router-dom';
import { MapPin, Navigation, Flame, AlertTriangle, Eye, Layers, X } from 'lucide-react';
import { getFlaggedAnomalies } from '../services/api';
import { useTranslation } from '../i18n/translations';

const GISMap = () => {
  const { activeRole, refreshKey, language } = useOutletContext();
  const navigate = useNavigate();
  const t = useTranslation(language || 'en');
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProject, setSelectedProject] = useState(null);
  const [mapReady, setMapReady] = useState(false);
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markersRef = useRef([]);

  // Load Leaflet dynamically
  useEffect(() => {
    if (window.L) {
      setMapReady(true);
      return;
    }

    const link = document.createElement('link');
    link.rel = 'stylesheet';
    link.href = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css';
    document.head.appendChild(link);

    const script = document.createElement('script');
    script.src = 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js';
    script.onload = () => setMapReady(true);
    document.body.appendChild(script);

    return () => {
      document.head.removeChild(link);
      document.body.removeChild(script);
    };
  }, []);

  // Fetch projects
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true);
        const data = await getFlaggedAnomalies({ limit: 200 });
        let filtered = data || [];
        if (activeRole === 'DISTRICT_OFFICER') {
          filtered = filtered.filter((p) => p.district_name === 'Varanasi');
        }
        setProjects(filtered);
      } catch (err) {
        console.error('Failed to load map data', err);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, [refreshKey, activeRole]);

  // Initialize map
  useEffect(() => {
    if (!mapReady || !mapRef.current || mapInstanceRef.current) return;

    const L = window.L;
    const map = L.map(mapRef.current, {
      center: [20.5937, 78.9629], // Center of India
      zoom: 5,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors',
      maxZoom: 18,
    }).addTo(map);

    mapInstanceRef.current = map;

    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [mapReady]);

  // Add markers
  useEffect(() => {
    if (!mapInstanceRef.current || !window.L || projects.length === 0) return;

    const L = window.L;
    const map = mapInstanceRef.current;

    // Clear existing markers
    markersRef.current.forEach((marker) => marker.remove());
    markersRef.current = [];

    projects.forEach((project) => {
      if (!project.sanctioned_latitude || !project.sanctioned_longitude) return;

      const lat = Number(project.sanctioned_latitude);
      const lon = Number(project.sanctioned_longitude);
      const riskScore = Number(project.risk_score || 0);
      const severity = project.severity || 'LOW';

      // Color based on severity
      const colorMap = {
        CRITICAL: '#ef4444',
        HIGH: '#f97316',
        MEDIUM: '#f59e0b',
        LOW: '#10b981',
      };
      const color = colorMap[severity] || '#06b6d4';

      // Create custom icon
      const icon = L.divIcon({
        className: 'custom-marker',
        html: `
          <div style="
            width: 32px;
            height: 32px;
            background: ${color};
            border: 3px solid white;
            border-radius: 50%;
            box-shadow: 0 4px 12px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            animation: ${severity === 'CRITICAL' ? 'pulse 2s infinite' : 'none'};
          ">
            <div style="width: 12px; height: 12px; background: white; border-radius: 50%;"></div>
          </div>
        `,
        iconSize: [32, 32],
        iconAnchor: [16, 32],
      });

      const marker = L.marker([lat, lon], { icon });

      // Popup content
      const popupContent = `
        <div style="min-width: 200px; font-family: system-ui; color: #1e293b;">
          <div style="font-weight: 700; font-size: 11px; color: #0891b2; margin-bottom: 4px;">${project.project_code}</div>
          <div style="font-weight: 600; font-size: 13px; margin-bottom: 8px; color: #0f172a;">${project.title}</div>
          <div style="display: flex; gap: 8px; margin-bottom: 8px; font-size: 11px;">
            <span style="background: ${color}20; color: ${color}; padding: 2px 8px; border-radius: 12px; font-weight: 700; border: 1px solid ${color}40;">
              ${severity}
            </span>
            <span style="color: #64748b;">Risk: ${riskScore.toFixed(1)}</span>
          </div>
          <div style="font-size: 11px; color: #64748b; margin-bottom: 4px;">
            <strong>District:</strong> ${project.district_name || 'N/A'}
          </div>
          ${
            project.geo_distance_meters > 500
              ? `<div style="font-size: 11px; color: #ef4444; margin-bottom: 4px;">
                  ⚠️ Geo Deviation: ${Number(project.geo_distance_meters).toFixed(0)}m
                </div>`
              : ''
          }
          <button
            onclick="window.openProjectInspector(${project.id})"
            style="
              width: 100%;
              margin-top: 8px;
              padding: 6px;
              background: #0891b2;
              color: white;
              border: none;
              border-radius: 6px;
              font-size: 11px;
              font-weight: 600;
              cursor: pointer;
            "
          >
            Open Forensic Desk →
          </button>
        </div>
      `;

      marker.bindPopup(popupContent, {
        maxWidth: 280,
        className: 'custom-popup',
      });

      marker.addTo(map);
      markersRef.current.push(marker);

      // Draw line if geo anomaly
      if (
        project.actual_latitude &&
        project.actual_longitude &&
        project.geo_distance_meters > 500
      ) {
        const actualLat = Number(project.actual_latitude);
        const actualLon = Number(project.actual_longitude);

        const line = L.polyline(
          [
            [lat, lon],
            [actualLat, actualLon],
          ],
          {
            color: '#ef4444',
            weight: 2,
            opacity: 0.7,
            dashArray: '5, 10',
          }
        );
        line.addTo(map);
        markersRef.current.push(line);

        // Add actual location marker
        const actualIcon = L.divIcon({
          className: 'custom-marker',
          html: `
            <div style="
              width: 24px;
              height: 24px;
              background: #fca5a5;
              border: 2px solid #ef4444;
              border-radius: 50%;
              box-shadow: 0 2px 8px rgba(239,68,68,0.4);
            "></div>
          `,
          iconSize: [24, 24],
          iconAnchor: [12, 24],
        });

        const actualMarker = L.marker([actualLat, actualLon], { icon: actualIcon });
        actualMarker.bindPopup(`<div style="font-size: 11px; color: #ef4444; font-weight: 600;">Actual Location (${project.geo_distance_meters.toFixed(0)}m deviation)</div>`);
        actualMarker.addTo(map);
        markersRef.current.push(actualMarker);
      }
    });

    // Global function for popup button
    window.openProjectInspector = (projectId) => {
      navigate(`/audit?id=${projectId}`);
    };
  }, [projects, navigate]);

  const getSeverityCounts = () => {
    return {
      CRITICAL: projects.filter((p) => p.severity === 'CRITICAL').length,
      HIGH: projects.filter((p) => p.severity === 'HIGH').length,
      MEDIUM: projects.filter((p) => p.severity === 'MEDIUM').length,
      LOW: projects.filter((p) => p.severity === 'LOW').length,
    };
  };

  const counts = getSeverityCounts();

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-extrabold text-white tracking-tight flex items-center gap-2.5">
            <MapPin className="w-6 h-6 text-cyan-400" />
            {t('geospatialIntelligence')}
          </h2>
          <p className="text-xs text-slate-400 mt-1">
            Real-time nationwide anomaly visualization with GPS deviation vectors, risk clustering, and forensic popups
          </p>
        </div>
      </div>

      {/* Legend Bar */}
      <div className="glass-card p-4 rounded-2xl border border-slate-800 flex items-center justify-between gap-4 flex-wrap">
        <div className="flex items-center gap-3">
          <Layers className="w-4 h-4 text-cyan-400" />
          <span className="text-xs font-semibold text-slate-300">{t('mapLegend')}:</span>
        </div>
        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-red-500 border-2 border-white"></div>
            <span className="text-xs text-slate-300">{t('critical')} ({counts.CRITICAL})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-orange-500 border-2 border-white"></div>
            <span className="text-xs text-slate-300">{t('high')} ({counts.HIGH})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-amber-500 border-2 border-white"></div>
            <span className="text-xs text-slate-300">{t('medium')} ({counts.MEDIUM})</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full bg-emerald-500 border-2 border-white"></div>
            <span className="text-xs text-slate-300">{t('low')} ({counts.LOW})</span>
          </div>
          <div className="flex items-center gap-2 ml-4">
            <div className="w-8 h-0.5 bg-red-500" style={{ borderTop: '2px dashed #ef4444' }}></div>
            <span className="text-xs text-slate-300">{t('geoDeviation')}</span>
          </div>
        </div>
        <div className="text-xs text-slate-400">
          {t('displaying')} <span className="font-bold text-cyan-400">{projects.length}</span> {t('flaggedWorks')}
        </div>
      </div>

      {/* Map Container */}
      <div className="flex-1 glass-card rounded-2xl border border-slate-800 overflow-hidden relative">
        {loading && (
          <div className="absolute inset-0 bg-slate-950/80 backdrop-blur-sm z-10 flex items-center justify-center">
            <div className="text-center">
              <div className="w-12 h-12 border-4 border-cyan-500 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
              <p className="text-sm font-semibold text-slate-300">{t('loadingGeospatial')}</p>
            </div>
          </div>
        )}
        {!mapReady && !loading && (
          <div className="absolute inset-0 flex items-center justify-center">
            <p className="text-sm text-slate-400">Initializing map engine...</p>
          </div>
        )}
        <div ref={mapRef} className="w-full h-full" />
      </div>

      <style>{`
        @keyframes pulse {
          0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
          50% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
        }
        .leaflet-popup-content-wrapper {
          border-radius: 12px !important;
          box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3) !important;
        }
        .leaflet-popup-tip {
          display: none !important;
        }
      `}</style>
    </div>
  );
};

export default GISMap;
