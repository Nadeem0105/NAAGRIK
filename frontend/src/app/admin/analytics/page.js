// f:\CN Hackathon\frontend\src\app\admin\analytics\page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import { LayoutDashboard, Flame, AlertTriangle, ArrowRight, RefreshCw, Trophy, Clock } from 'lucide-react';
import { useRouter } from 'next/navigation';
import styles from '../page.module.css';
import { useApp } from '@/context/AppContext';
import dynamic from 'next/dynamic';

// Dynamically import the HotspotMap component to prevent SSR issues with Leaflet
const HotspotMap = dynamic(() => import('@/components/MapPreview').then(mod => {
  // If we want to use the HotspotMap we created:
  return import('@/components/HotspotMap');
}), { ssr: false });

export default function MunicipalAnalyticsPage() {
  const router = useRouter();
  const { user, loading: userLoading } = useApp();
  
  const [impactStats, setImpactStats] = useState({
    total_reported: 0,
    total_resolved: 0,
    resolution_rate: 0,
    avg_resolution_time_hours: 0
  });
  const [hotspots, setHotspots] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [criticalIssues, setCriticalIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Allow any admin role (super, state, district)
  useEffect(() => {
    if (!userLoading) {
      const isAdmin = user?.role === 'admin' || user?.is_admin;
      if (!isAdmin) {
        router.replace('/portal');
      }
    }
  }, [user, userLoading, router]);

  const loadAnalyticsData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      // 1. Fetch scoped impact stats
      const stats = await api.getImpactStats();
      setImpactStats(stats || {
        total_reported: 0,
        total_resolved: 0,
        resolution_rate: 0,
        avg_resolution_time_hours: 0
      });

      // 2. Fetch scoped hotspots
      const spots = await api.getHotspots();
      setHotspots(spots || []);

      // 3. Fetch scoped department performance
      const depts = await api.getDepartmentPerformance();
      setDepartments(depts || []);

      // 4. Fetch critical SLA issues in the admin's scope
      const issuesRes = await api.adminListIssues({ severity: 'high', limit: 20 });
      setCriticalIssues(issuesRes.items || issuesRes || []);

    } catch (err) {
      console.error('Failed to load analytics data:', err);
      setError(err.message || 'Failed to load analytics data. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user) {
      loadAnalyticsData();
    }
  }, [user, loadAnalyticsData]);

  if (userLoading || !user || (user.role !== 'admin' && !user.is_admin)) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}>
        <div className="utility-code">Verifying admin access...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Top Status Header */}
      <header className={styles.pageHeader}>
        <div>
          <span className="label-caps text-outline">ANALYTICS PORTAL</span>
          <h2 className={styles.pageTitle}>Municipal Analytics</h2>
        </div>
        <div className={styles.systemStatus}>
          <button className="blueprint-btn blueprint-btn-secondary mr-4" onClick={loadAnalyticsData} disabled={loading}>
            <RefreshCw size={14} className={loading ? styles.spinner : ''} />
            <span>REFRESH</span>
          </button>
          <span className="utility-code text-success-green flex items-center gap-2">
            <span className={styles.statusPulseDot}></span> LIVE ANALYTICS
          </span>
        </div>
      </header>

      {error && (
        <div className={styles.errorAlert} style={{ marginTop: '24px' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className={styles.tabContainer} style={{ marginTop: '24px' }}>
        {/* Quick Metrics */}
        <div className={styles.metricsRow}>
          <div className={`${styles.metricCard} blueprint-card`}>
            <span className="label-caps text-outline">TOTAL INCIDENTS</span>
            <div className={styles.metricVal}>{impactStats.total_reported}</div>
          </div>
          <div className={`${styles.metricCard} blueprint-card`}>
            <span className="label-caps text-outline">RESOLUTION RATE</span>
            <div className={styles.metricVal}>{Math.round(impactStats.resolution_rate)}%</div>
          </div>
          <div className={`${styles.metricCard} blueprint-card`}>
            <span className="label-caps text-outline">AVG RESOLUTION</span>
            <div className={styles.metricVal}>
              {impactStats.avg_resolution_time_hours > 0 
                ? `${Math.round(impactStats.avg_resolution_time_hours)}h` 
                : 'N/A'}
            </div>
          </div>
          <div className={`${styles.metricCard} blueprint-card`}>
            <span className="label-caps text-outline">ACTIVE HOTSPOTS</span>
            <div className={styles.metricVal}>{hotspots.length}</div>
          </div>
        </div>

        {/* Dashboard Grid */}
        <div className={styles.dashGrid}>
          {/* Left Column: Critical SLA Dispatches */}
          <div className={styles.criticalCol}>
            <div className={styles.sectionTitleRow}>
              <span className="label-caps text-outline">CRITICAL SLA DISPATCHES</span>
              <div className={styles.line}></div>
            </div>

            <div className={styles.criticalList}>
              {criticalIssues.filter(i => i.status !== 'resolved').map(issue => (
                <div key={issue.id} className={`${styles.criticalItem} blueprint-card`}>
                  <div className={styles.itemMeta}>
                    <span className="utility-code text-outline">{issue.id?.slice(0, 8).toUpperCase()}</span>
                    <span className="label-caps text-error">CRITICAL SLA</span>
                  </div>
                  <h4 className={styles.criticalTitle}>{issue.title}</h4>
                  <p className={styles.criticalDesc}>{issue.description}</p>
                  <button className="blueprint-btn blueprint-btn-secondary" onClick={() => router.push('/admin')}>
                    <span>DISPATCH OR ASSIGN</span>
                    <ArrowRight size={14} />
                  </button>
                </div>
              ))}

              {criticalIssues.filter(i => i.status !== 'resolved').length === 0 && !loading && (
                <div className="blueprint-card p-6 text-center text-outline">
                  <span className="utility-code">No active high-severity issues found</span>
                </div>
              )}
            </div>

            {/* Department Leaderboard */}
            <div className={styles.sectionTitleRow} style={{ marginTop: '32px' }}>
              <span className="label-caps text-outline">DEPARTMENT PERFORMANCE</span>
              <div className={styles.line}></div>
            </div>

            <div className="blueprint-card" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {departments.length === 0 ? (
                <div className="text-center text-outline py-4">
                  <span className="utility-code">No department data available</span>
                </div>
              ) : (
                departments.map((dept, index) => (
                  <div key={dept.id || index} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '8px', borderBottom: '1px solid var(--keyline)' }}>
                    <div>
                      <div style={{ fontWeight: 'bold', fontSize: '14px' }}>{dept.name}</div>
                      <div className="utility-code" style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
                        Assigned: {dept.assigned_count} | Resolved: {dept.resolved_count}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 'bold', color: 'var(--route-blue)' }}>
                        {Math.round(dept.resolution_rate)}% Rate
                      </div>
                      <div className="utility-code" style={{ fontSize: '11px', color: 'var(--ink-secondary)' }}>
                        Avg: {dept.avg_resolution_time_hours > 0 ? `${Math.round(dept.avg_resolution_time_hours)}h` : 'N/A'}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Right Column: Live Coordinates / Hotspots Map */}
          <div className={styles.mapCol}>
            <div className={styles.sectionTitleRow}>
              <span className="label-caps text-outline">LIVE HOTSPOT MONITOR</span>
              <div className={styles.line}></div>
            </div>
            <div className={styles.liveMapPlaceholder} style={{ height: '450px', padding: 0, border: '1px solid var(--keyline)', overflow: 'hidden', position: 'relative' }}>
              {!loading && (
                <HotspotMap hotspots={hotspots} />
              )}
              {loading && (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%', width: '100%', gap: '12px' }}>
                  <RefreshCw size={24} className={styles.spinner} />
                  <span className="utility-code">LOADING SPATIAL ENGINE...</span>
                </div>
              )}
            </div>
            
            <div style={{ marginTop: '16px' }} className="blueprint-card p-4">
              <h4 style={{ margin: '0 0 8px 0', fontSize: '14px', fontWeight: 'bold' }} className="label-caps text-outline">DBSCAN Clustering Active</h4>
              <p style={{ margin: 0, fontSize: '13px', lineHeight: '1.5', color: 'var(--ink-secondary)' }}>
                Spatial clusters are dynamically calculated using the Density-Based Spatial Clustering of Applications with Noise (DBSCAN) algorithm. 
                Clusters represent high-density reporting zones within {user.admin_scope ? `your assigned ${user.admin_scope}` : 'the state'} region, helping identify recurring infrastructure issues.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
