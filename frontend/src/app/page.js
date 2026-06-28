// f:\CN Hackathon\frontend\src\app\page.js
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import dynamic from 'next/dynamic';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';
import { 
  Activity, 
  Shield, 
  CheckCircle2, 
  Clock, 
  BarChart3, 
  ArrowRight,
  Camera,
  Sparkles,
  Users,
  GitCommit,
  Trophy,
  Map,
  AlertTriangle,
  Wrench
} from 'lucide-react';
import styles from './page.module.css';

// Dynamically import the MapPreview component to prevent SSR issues with Leaflet
const MapPreview = dynamic(() => import('@/components/MapPreview'), { ssr: false });

const MOCK_ISSUES = [
  { id: 'mock-1', latitude: 12.9782, longitude: 77.6435, status: 'assigned' },
  { id: 'mock-2', latitude: 12.9611, longitude: 77.5855, status: 'resolved' },
  { id: 'mock-3', latitude: 12.9912, longitude: 77.5912, status: 'reported' },
  { id: 'mock-4', latitude: 12.9562, longitude: 77.6201, status: 'in_progress' },
  { id: 'mock-5', latitude: 12.9750, longitude: 77.6010, status: 'resolved' }
];

export default function LandingPage() {
  const { user } = useApp();
  const [stats, setStats] = useState(null);
  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, issuesData] = await Promise.all([
          api.getImpactStats(),
          api.listIssues({ limit: 15 })
        ]);
        setStats(statsData);
        if (issuesData && issuesData.items && issuesData.items.length > 0) {
          setIssues(issuesData.items);
        } else {
          setIssues(MOCK_ISSUES);
        }
      } catch (err) {
        console.error('Failed to load data, using fallbacks:', err);
        setStats({
          total_reported: 0,
          total_resolved: 0,
          avg_resolution_time_hours: 0,
          category_breakdown: {
            "Infrastructure": 0,
            "Sanitation": 0,
            "Public Safety": 0
          },
          status_breakdown: {
            "reported": 0,
            "in_progress": 0,
            "resolved": 0
          }
        });
        setIssues(MOCK_ISSUES);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  const resolutionRate = stats 
    ? Math.round((stats.total_resolved / Math.max(stats.total_reported, 1)) * 100) 
    : 0;

  return (
    <div className={styles.pageWrapper}>
      <div className={styles.container}>
        
        {/* HERO SECTION */}
        <section className={styles.heroSection}>
          <div className={styles.civicBadge}>
            <Shield size={14} />
            <span className="label-caps">
              {stats ? `${stats.total_reported.toLocaleString()} ISSUES REPORTED` : '14,320 ISSUES REPORTED'} THIS WEEK
            </span>
          </div>
          <h1 className={styles.heroTitle}>NAGARIK</h1>
          <p className={styles.heroSubtitle}>
            Community issue reporting for your city
          </p>
          <p className={styles.heroDescription}>
            Nagarik lets anyone report a pothole, leak, or broken streetlight in minutes, then follow exactly what the city does about it, all the way through to resolved.
          </p>
          
          <div className={styles.ctaGroup}>
            {user ? (
              <Link href="/portal" className="blueprint-btn blueprint-btn-primary">
                <span>ENTER CITIZEN PORTAL</span>
                <ArrowRight size={16} />
              </Link>
            ) : (
              <>
                <Link href="/login" className="blueprint-btn blueprint-btn-primary">
                  <span>SIGN IN</span>
                  <ArrowRight size={16} />
                </Link>
                <Link href="/register" className="blueprint-btn blueprint-btn-secondary">
                  <span>JOIN NOW</span>
                </Link>
              </>
            )}
          </div>
        </section>

        {/* MAP PREVIEW SECTION */}
        <section className={styles.mapSection}>
          <div className={styles.mapCard}>
            <div className={styles.mapHeader}>
              <span className={styles.mapTitle}>Map Preview</span>
              <span className={styles.mapSub}>Live issue map</span>
            </div>
            
            <div className={styles.mapBody}>
              <MapPreview issues={issues} />
            </div>

            {/* Legend */}
            <div className={styles.mapLegend}>
              <div className={styles.legendItem}>
                <div className={`${styles.legendColor} ${styles.bgPinCritical}`}></div>
                <span className={styles.legendText}>Alert (Critical)</span>
              </div>
              <div className={styles.legendItem}>
                <div className={`${styles.legendColor} ${styles.bgPinAlert}`}></div>
                <span className={styles.legendText}>In Progress</span>
              </div>
              <div className={styles.legendItem}>
                <div className={`${styles.legendColor} ${styles.bgPinResolved}`}></div>
                <span className={styles.legendText}>Resolved</span>
              </div>
            </div>
          </div>
        </section>

        {/* FEATURES SECTION */}
        <section className={styles.featuresSection}>
          <div className={styles.featuresContainer}>
            <div className={styles.featuresHeader}>
              <div className={styles.featuresHeaderLine}></div>
              <span className={styles.featuresSubtitle}>What Nagarik does</span>
              <h2 className={styles.featuresTitle}>Built for civic action</h2>
            </div>

            <div className={styles.featuresGrid}>
              {/* Feature 1 */}
              <div className={styles.featureCard}>
                <div className={styles.featureIconWrapper}>
                  <Camera size={20} />
                </div>
                <h3 className={styles.featureCardTitle}>Report instantly</h3>
                <p className={styles.featureCardDesc}>
                  Snap a photo, drop a pin, and submit a report in under a minute.
                </p>
              </div>

              {/* Feature 2 */}
              <div className={styles.featureCard}>
                <div className={styles.featureIconWrapper}>
                  <Sparkles size={20} />
                </div>
                <h3 className={styles.featureCardTitle}>AI does the sorting</h3>
                <p className={styles.featureCardDesc}>
                  Every report gets categorized, scored for severity, and routed to the right department automatically.
                </p>
              </div>

              {/* Feature 3 */}
              <div className={styles.featureCard}>
                <div className={styles.featureIconWrapper}>
                  <Users size={20} />
                </div>
                <h3 className={styles.featureCardTitle}>Community verifies</h3>
                <p className={styles.featureCardDesc}>
                  Neighbors confirm real issues and flag duplicates before they ever reach an admin queue.
                </p>
              </div>

              {/* Feature 4 */}
              <div className={styles.featureCard}>
                <div className={styles.featureIconWrapper}>
                  <GitCommit size={20} />
                </div>
                <h3 className={styles.featureCardTitle}>Track it live</h3>
                <p className={styles.featureCardDesc}>
                  Follow any issue from reported to resolved, with a public timeline every step of the way.
                </p>
              </div>

              {/* Feature 5 */}
              <div className={styles.featureCard}>
                <div className={styles.featureIconWrapper}>
                  <Trophy size={20} />
                </div>
                <h3 className={styles.featureCardTitle}>Get recognized</h3>
                <p className={styles.featureCardDesc}>
                  Earn points and badges for reporting, verifying, and helping your city improve.
                </p>
              </div>

              {/* Feature 6 */}
              <div className={styles.featureCard}>
                <div className={styles.featureIconWrapper}>
                  <Map size={20} />
                </div>
                <h3 className={styles.featureCardTitle}>Local accountability</h3>
                <p className={styles.featureCardDesc}>
                  State and district admins are scoped to their own jurisdiction, so every report reaches someone actually responsible for it.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* IMPACT METRICS SECTION */}
        <section className={styles.statsSection}>
          <div className={styles.sectionHeader}>
            <span className="label-caps">Impact metrics</span>
            <h2 className={styles.sectionTitle}>City-wide progress</h2>
          </div>

          {loading ? (
            <div className={styles.loadingStats}>
              <span className="utility-code">Loading impact data...</span>
            </div>
          ) : (
            <>
              <div className={styles.statsGrid}>
                {/* KPI 1: Total Resolved */}
                <div className={styles.statCard}>
                  <div className={styles.statCardHeader}>
                    <span className={styles.statTitle}>Total resolved</span>
                    <CheckCircle2 size={16} className={styles.successIcon} />
                  </div>
                  <div className={styles.statValue}>
                    {stats.total_resolved} of {stats.total_reported} reported
                  </div>
                  <div className={styles.progressBarWrapper}>
                    <div 
                      className={styles.progressBar} 
                      style={{ width: `${resolutionRate}%` }}
                    ></div>
                  </div>
                </div>

                {/* KPI 2: Resolution Rate */}
                <div className={styles.statCard}>
                  <div className={styles.statCardHeader}>
                    <span className={styles.statTitle}>Resolution rate</span>
                    <Activity size={16} className={styles.infoIcon} />
                  </div>
                  <div className={styles.statValueGroup}>
                    <span className={styles.statNumber}>{resolutionRate}%</span>
                    <span className={styles.statSub}>target 90%</span>
                  </div>
                  <div className={styles.progressBarWrapper}>
                    <div 
                      className={styles.progressBar} 
                      style={{ width: `${resolutionRate}%`, backgroundColor: 'var(--signal-amber)' }}
                    ></div>
                  </div>
                </div>

                {/* KPI 3: Avg Resolution */}
                <div className={styles.statCard}>
                  <div className={styles.statCardHeader}>
                    <span className={styles.statTitle}>Avg resolution</span>
                    <Clock size={16} className={styles.warningIcon} />
                  </div>
                  <div className={styles.statValue}>
                    {Math.round(stats.avg_resolution_time_hours)}h
                  </div>
                  <div className={styles.statTrend}>
                    ↓ vs 240h last month
                  </div>
                </div>
              </div>

              {/* Detailed Breakdown */}
              {stats && (
                <div className={styles.detailsGrid}>
                  {/* Category Breakdown */}
                  <div className={styles.detailsCard}>
                    <div className={styles.detailsCardHeader}>
                      <span className={styles.detailsCardTitle}>Category Breakdown</span>
                    </div>
                    <div className={styles.breakdownList}>
                      {Object.entries(stats.category_breakdown).map(([category, count]) => {
                        const pct = Math.round((count / Math.max(stats.total_reported, 1)) * 100);
                        return (
                          <div key={category} className={styles.breakdownItem}>
                            <div className={styles.breakdownText}>
                              <span className={styles.breakdownLabel}>{category}</span>
                              <span className={styles.breakdownVal}>{count} ({pct}%)</span>
                            </div>
                            <div className={styles.barContainer}>
                              <div className={styles.barFill} style={{ width: `${pct}%` }}></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>

                  {/* Resolution Status */}
                  <div className={styles.detailsCard}>
                    <div className={styles.detailsCardHeader}>
                      <span className={styles.detailsCardTitle}>Resolution Status</span>
                    </div>
                    <div className={styles.breakdownList}>
                      {Object.entries(stats.status_breakdown).map(([status, count]) => {
                        const pct = Math.round((count / Math.max(stats.total_reported, 1)) * 100);
                        const formattedStatus = status.replace('_', ' ').toUpperCase();
                        return (
                          <div key={status} className={styles.breakdownItem}>
                            <div className={styles.breakdownText}>
                              <span className={styles.breakdownLabel}>{formattedStatus}</span>
                              <span className={styles.breakdownVal}>{count.toLocaleString()} ({pct}%)</span>
                            </div>
                            <div className={styles.barContainer}>
                              <div 
                                className={styles.barFill} 
                                style={{ 
                                  width: `${pct}%`, 
                                  backgroundColor: status === 'resolved' ? 'var(--success-green)' : status === 'in_progress' ? 'var(--signal-amber)' : 'var(--ink-secondary)'
                                }}
                              ></div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              )}
            </>
          )}
        </section>

        {/* SYSTEM SUMMARY FOOTER */}
        <footer className={styles.footer}>
          <div className={styles.footerContent}>
            <span>Municipal reporting system.</span>
          </div>
        </footer>

      </div>
    </div>
  );
}
