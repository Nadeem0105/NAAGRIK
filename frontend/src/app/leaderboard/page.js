// f:\CN Hackathon\frontend\src\app\leaderboard\page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import { useApp } from '@/context/AppContext';
import { Award, Flame, Zap, ShieldCheck, Download, MapPin, Loader2 } from 'lucide-react';
import styles from './page.module.css';

export default function LeaderboardPage() {
  const { user, fetchUser } = useApp();
  const [leaders, setLeaders] = useState([]);
  const [scope, setScope] = useState(null);
  const [viewerRank, setViewerRank] = useState(null);
  const [states, setStates] = useState([]);
  const [selectedStateId, setSelectedStateId] = useState('');
  const [loading, setLoading] = useState(true);
  const [savingState, setSavingState] = useState(false);
  const [error, setError] = useState('');
  const [onboardingStateId, setOnboardingStateId] = useState('');
  
  // For Super Admin state switching
  const [adminSelectedState, setAdminSelectedState] = useState('global');

  // Load list of states for onboarding / admin dropdown
  useEffect(() => {
    async function loadStates() {
      try {
        const data = await api.getStates();
        setStates(data);
      } catch (err) {
        console.error('Failed to load states:', err);
      }
    }
    loadStates();
  }, []);

  const loadLeaderboard = useCallback(async (stateId = null) => {
    setLoading(true);
    setError('');
    try {
      // If stateId is 'global', pass null
      const actualStateId = stateId === 'global' ? null : stateId;
      const data = await api.getLeaderboard(50, actualStateId);
      setLeaders(data.entries || []);
      setScope(data.scope || null);
      setViewerRank(data.viewer_rank || null);
    } catch (err) {
      console.error('Failed to load leaderboard:', err);
      setError(err.message || 'Failed to load leaderboard. Please try again.');
      setLeaders([]);
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch leaderboard based on user role/state or admin selection
  useEffect(() => {
    if (user?.role === 'super_admin') {
      loadLeaderboard(adminSelectedState);
    } else {
      loadLeaderboard(null);
    }
  }, [user, adminSelectedState, loadLeaderboard]);

  const handleOnboardingSubmit = async (e) => {
    e.preventDefault();
    if (!onboardingStateId) return;
    setSavingState(true);
    try {
      await api.updateMyState(onboardingStateId);
      await fetchUser(); // Refresh user context
      await loadLeaderboard(null);
    } catch (err) {
      console.error('Failed to update state:', err);
      setError(err.message || 'Failed to update state. Please try again.');
    } finally {
      setSavingState(false);
    }
  };

  const isCitizenWithoutState = user && user.role === 'citizen' && !user.state_id;

  // Determine header label
  let scopeLabel = 'ALL STATES';
  if (scope) {
    if (scope.type === 'state') {
      scopeLabel = `STATE RANKINGS: ${scope.state_name || 'LOCAL'}`;
    } else if (scope.type === 'district') {
      scopeLabel = `DISTRICT RANKINGS: ${scope.district_name || 'LOCAL'}`;
    }
  }

  return (
    <div className={`${styles.leaderboardWrapper} blueprint-bg`}>
      <div className={styles.container}>
        
        {/* Header */}
        <header className={`${styles.header} animate-fade-in-up`}>
          <span className="label-caps text-route-blue">CIVIC METRICS DATABASE</span>
          <h1 className={styles.title}>Contribution Leaderboard</h1>
          <p className={styles.subtitle}>
            Official ranking of citizens and administrators based on validated field reports, issue resolutions, and consistent civic engagement within the municipal grid.
          </p>
        </header>

        {/* Onboarding Gate for Citizens without State */}
        {isCitizenWithoutState && (
          <div className={`${styles.onboardingCard} animate-scale-up`}>
            <div className={styles.scopeLabel}>DIVISION REGISTRATION REQUIRED</div>
            <h2 className={styles.onboardingTitle}>Select Your State to Join</h2>
            <p className={styles.onboardingText}>
              To view localized rankings, earn badges, and compete with other citizens in your region, please select your state. You won't appear on the leaderboard until this is set.
            </p>
            <form onSubmit={handleOnboardingSubmit} className={styles.onboardingForm}>
              <select
                className={styles.stateSelect}
                value={onboardingStateId}
                onChange={(e) => setOnboardingStateId(e.target.value)}
                disabled={savingState}
                required
              >
                <option value="">-- SELECT STATE --</option>
                {states.map((s) => (
                  <option key={s.id} value={s.id}>
                    {s.name}
                  </option>
                ))}
              </select>
              <button
                type="submit"
                className="blueprint-btn"
                disabled={savingState || !onboardingStateId}
              >
                {savingState ? (
                  <>
                    <Loader2 size={14} className="animate-spin mr-2" />
                    <span>SAVING...</span>
                  </>
                ) : (
                  <span>CONFIRM STATE & JOIN</span>
                )}
              </button>
            </form>
          </div>
        )}

        <div className={styles.grid}>
          <main className={`${styles.mainContent} animate-fade-in-up delay-100`}>
            
            {/* Super Admin State Filter / Scope Label Row */}
            <div className={styles.adminFilterRow}>
              <div>
                <span className={styles.scopeLabel}>{scopeLabel}</span>
              </div>
              
              {user?.role === 'super_admin' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span className="label-caps" style={{ fontSize: '11px' }}>Filter:</span>
                  <select
                    className={styles.stateSelect}
                    style={{ minWidth: '180px', padding: '6px 12px' }}
                    value={adminSelectedState}
                    onChange={(e) => setAdminSelectedState(e.target.value)}
                  >
                    <option value="global">GLOBAL (ALL STATES)</option>
                    {states.map((s) => (
                      <option key={s.id} value={s.id}>
                        {s.name}
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>

            {/* Leaderboard Table Container */}
            <div className={styles.leaderboardContainerRelative}>
              <div className={`${styles.leaderboardCard} ${isCitizenWithoutState ? styles.blurredContainer : ''}`}>
                <div className={styles.tableHeader}>
                  <span className="label-caps">RANK</span>
                  <span className="label-caps">NAME / REGION</span>
                  <span className="label-caps">ROLE</span>
                  <span className="label-caps text-right">CIVIC POINTS</span>
                </div>

                {loading ? (
                  <div className={styles.loader}>
                    <span className="utility-code">Loading leaderboard metrics...</span>
                  </div>
                ) : leaders.length === 0 ? (
                  <div className={styles.emptyState}>
                    <span className="utility-code">
                      No reports filed in {scope?.state_name || 'this state'} yet. Be the first.
                    </span>
                  </div>
                ) : (
                  <div className={styles.tableBody}>
                    {leaders.map((leader, index) => {
                      const isTopThree = leader.rank <= 3;
                      const delayClass = `delay-${Math.min((index + 1) * 100, 800)}`;
                      return (
                        <div
                          key={leader.user_id}
                          className={`${styles.row} ${isTopThree ? `${styles.topThreeRow} animate-pulse-glow` : ''} animate-fade-in-up ${delayClass}`}
                        >
                          <div className={`${styles.rankCol} utility-code ${isTopThree ? styles.amberText : ''}`} style={{ fontFamily: 'var(--font-mono)' }}>
                            #{String(leader.rank).padStart(2, '0')}
                          </div>
                          <div className={styles.nameCol}>
                            <div className={styles.avatarPlaceholder} style={isTopThree ? { borderColor: '#f59e0b', color: '#f59e0b' } : {}}>
                              <span>{(leader.display_name || '?')[0].toUpperCase()}</span>
                            </div>
                            <div>
                              <span className={styles.leaderName} style={isTopThree ? { fontWeight: '700' } : {}}>
                                {leader.display_name}
                              </span>
                              {leader.state_name && (
                                <div style={{ fontSize: '11px', color: 'var(--ink-secondary)', display: 'flex', alignItems: 'center', gap: '2px', marginTop: '2px' }}>
                                  <MapPin size={10} />
                                  <span>{leader.state_name}</span>
                                </div>
                              )}
                            </div>
                          </div>
                          <div className={styles.badgeCol}>
                            <span className="label-caps" style={{ fontSize: '11px', fontWeight: '600', color: leader.role === 'citizen' ? 'var(--ink-secondary)' : 'var(--route-blue)' }}>
                              {leader.role.replace('_', ' ')}
                            </span>
                          </div>
                          <div className={`${styles.scoreCol} utility-code ${isTopThree ? styles.amberText : ''}`} style={{ fontFamily: 'var(--font-mono)' }}>
                            {leader.civic_points.toLocaleString()}
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>

              {/* Blurred locked overlay if citizen has no state */}
              {isCitizenWithoutState && (
                <div className={styles.lockedOverlay}>
                  <div className={styles.lockedOverlayCard}>
                    <span className="label-caps text-outline block mb-2">ACCESS RESTRICTED</span>
                    <p className="utility-code" style={{ fontSize: '12px', marginBottom: '16px' }}>
                      Please select your state in the division registration card above to unlock and view the leaderboard.
                    </p>
                  </div>
                </div>
              )}
            </div>

          </main>

          <aside className={styles.sideContent}>
            
            {/* Scoring method */}
            <div className={`${styles.sideCard} blueprint-card animate-slide-in-right delay-200`}>
              <span className="label-caps mb-4 block">SCORING METHODOLOGY</span>
              <ul className={styles.methodList}>
                <li className={styles.methodItem}>
                  <Zap size={16} className={styles.methodIcon} />
                  <div>
                    <div className={styles.methodName}>New Report</div>
                    <span className="utility-code text-outline">50 PTS</span>
                  </div>
                </li>
                <li className={styles.methodItem}>
                  <Award size={16} className={styles.methodIcon} />
                  <div>
                    <div className={styles.methodName}>Issue Resolved</div>
                    <span className="utility-code text-outline">200 PTS</span>
                  </div>
                </li>
                <li className={styles.methodItem}>
                  <ShieldCheck size={16} className={styles.methodIcon} />
                  <div>
                    <div className={styles.methodName}>Validation</div>
                    <span className="utility-code text-outline">10 PTS</span>
                  </div>
                </li>
              </ul>
            </div>

            {/* Active protocols */}
            <div className={`${styles.sideCard} blueprint-card animate-slide-in-right delay-300`}>
              <span className="label-caps mb-4 block">ACTIVE PROTOCOLS</span>
              <div className={styles.protocolCard}>
                <div className={styles.protocolTitle}>Operation Clear Path</div>
                <p className={styles.protocolDesc}>
                  Double points for sidewalk obstruction reports this week.
                </p>
                <div className={styles.progressBarBg}>
                  <div className={styles.progressBarFill} style={{ width: '65%' }}></div>
                </div>
                <span className="utility-code text-outline mt-2 block text-right">65% TO TARGET</span>
              </div>
            </div>

          </aside>
        </div>

      </div>

      {/* Sticky Footer Viewer Rank Card */}
      {user && !isCitizenWithoutState && viewerRank && (
        <div className={`${styles.stickyFooter} animate-fade-in-up delay-500`}>
          <div className={styles.stickyFooterContent}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
              <div>
                <span className="label-caps text-outline block" style={{ fontSize: '10px' }}>YOUR RANK</span>
                <span className="utility-code" style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: '700' }}>
                  #{String(viewerRank.rank).padStart(2, '0')}
                </span>
              </div>
              <div style={{ width: '1px', height: '32px', background: 'var(--keyline)' }}></div>
              <div>
                <span className="label-caps block" style={{ fontSize: '14px', fontWeight: '600' }}>{user.name}</span>
                <span className="label-caps" style={{ fontSize: '10px', color: 'var(--ink-secondary)' }}>
                  {scope?.type === 'state' ? `${scope.state_name} DIVISION` : 'GLOBAL SCOPE'}
                </span>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <span className="label-caps text-outline block" style={{ fontSize: '10px' }}>TOTAL POINTS</span>
              <span className="utility-code" style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: '700', color: 'var(--route-blue)' }}>
                {viewerRank.civic_points.toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
