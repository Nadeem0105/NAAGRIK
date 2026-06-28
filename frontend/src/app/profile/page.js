// f:\CN Hackathon\frontend\src\app\profile\page.js
'use client';

import React, { useState, useEffect } from 'react';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';
import { useRouter } from 'next/navigation';
import { 
  User, MapPin, Award, Flame, Calendar, 
  ArrowRight, ShieldAlert, ShieldCheck, Lock, CheckCircle2 
} from 'lucide-react';
import styles from './page.module.css';

export default function ProfilePage() {
  const { user } = useApp();
  const router = useRouter();

  const [badges, setBadges] = useState([]);
  const [userIssues, setUserIssues] = useState([]);
  const [loading, setLoading] = useState(true);

  // All known badge templates to display on shelf (active vs locked)
  const BADGES_SHELF_TEMPLATES = [
    { name: "First Reporter", description: "Reported your first local civic issue!", type: "reports_count" },
    { name: "Local Watchdog", description: "Reported 10 civic issues to help your city.", type: "reports_count" },
    { name: "Community Hero", description: "Reported 50 civic issues! Outstanding contribution.", type: "reports_count" },
    { name: "Active Verifier", description: "Verified/upvoted 10 other citizens' reports.", type: "verifications_count" },
    { name: "Problem Solver", description: "Have 5 of your reported issues fully resolved by the city.", type: "resolved_reports" }
  ];

  useEffect(() => {
    if (!user) {
      router.push('/login');
      return;
    }
    if (user.role === 'admin') {
      router.push('/admin');
      return;
    }

    async function loadProfileStats() {
      try {
        // Fetch user badges
        try {
          const badgeData = await api.getUserBadges(user.id);
          setBadges(badgeData.items || badgeData || []);
        } catch (badgeErr) {
          console.error('Failed to load user badges:', badgeErr);
        }

        // Fetch citizen reported issues
        try {
          const issuesData = await api.listIssues();
          const reportedByMe = (issuesData.items || issuesData || []).filter(
            item => item.reporter_id === user.id
          );
          setUserIssues(reportedByMe);
        } catch (issueErr) {
          console.error('Failed to load user issues:', issueErr);
        }

      } catch (err) {
        console.error('Profile load error:', err);
      } finally {
        setLoading(false);
      }
    }

    loadProfileStats();
  }, [user, router]);

  if (!user) return null;

  // Determine user tier and progress
  const points = user.points || 0;
  let currentTier = 'Novice';
  let nextTier = 'Citizen Watchman';
  let minPoints = 0;
  let maxPoints = 100;

  if (points >= 1000) {
    currentTier = 'Sentinel';
    nextTier = 'Supreme Overseer';
    minPoints = 1000;
    maxPoints = 2500;
  } else if (points >= 600) {
    currentTier = 'Civic Hero';
    nextTier = 'Sentinel';
    minPoints = 600;
    maxPoints = 1000;
  } else if (points >= 300) {
    currentTier = 'Guardian';
    nextTier = 'Civic Hero';
    minPoints = 300;
    maxPoints = 600;
  } else if (points >= 100) {
    currentTier = 'Citizen Watchman';
    nextTier = 'Guardian';
    minPoints = 100;
    maxPoints = 300;
  }

  const tierProgressPct = Math.min(
    Math.max(((points - minPoints) / (maxPoints - minPoints)) * 100, 0),
    100
  );

  const getBadgeStatus = (badgeName) => {
    return badges.some(b => b.name.toLowerCase() === badgeName.toLowerCase());
  };

  return (
    <div className={styles.profileWrapper}>
      <div className={styles.container}>
        
        {/* Profile Header Identity */}
        <div className="blueprint-header">
          <p className="label-caps eyebrow">Citizen Profile</p>
          <h1 className={styles.title}>District Dashboard</h1>
        </div>

        {/* Profile Card & Points Gauge Row */}
        <div className={styles.profileMetaGrid}>
          
          {/* Identity Info Card */}
          <div className={`${styles.identityCard} blueprint-card`}>
            <div className={styles.identityHeader}>
              <div className={styles.avatarBox}>
                <User size={36} className={styles.avatarIcon} />
              </div>
              <div>
                <h2 className={styles.userName}>{user.name}</h2>
                <div className={styles.metaRow}>
                  <MapPin size={14} className={styles.metaIcon} />
                  <span>Ward 7 / Central District</span>
                </div>
              </div>
            </div>
            <div className={styles.identityDetails}>
              <div className={styles.detailRow}>
                <span className="label-caps">Role Status:</span>
                <span className="utility-code text-route-blue">{user.role?.toUpperCase() || 'CITIZEN'}</span>
              </div>
              <div className={styles.detailRow}>
                <span className="label-caps">User ID:</span>
                <span className="utility-code text-outline">{user.id?.slice(0, 13)}...</span>
              </div>
              <div className={styles.detailRow}>
                <span className="label-caps">Registration Date:</span>
                <span className="utility-code">{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
            </div>
          </div>

          {/* Points Progress Gauge Card */}
          <div className={`${styles.gaugeCard} blueprint-card`}>
            <div className={styles.gaugeHeader}>
              <div>
                <span className="label-caps">COMMUNITY TIER</span>
                <h3 className={styles.tierTitle}>{currentTier}</h3>
              </div>
              <Award size={28} className={styles.gaugeHeaderIcon} />
            </div>

            <div className={styles.gaugeScoreGroup}>
              <span className={styles.gaugeScoreNumber}>{points}</span>
              <span className={`${styles.gaugeScoreUnit} label-caps`}>Impact Points</span>
            </div>

            <div className={styles.progressContainer}>
              <div className={styles.progressHeader}>
                <span className="utility-code">{points} / {maxPoints} PTS</span>
                <span className="utility-code">{Math.round(tierProgressPct)}% to {nextTier}</span>
              </div>
              <div className={styles.progressBarBg}>
                <div 
                  className={styles.progressBarFill} 
                  style={{ width: `${tierProgressPct}%` }}
                ></div>
              </div>
            </div>
          </div>

        </div>

        {/* Badge Accolade Shelf */}
        <section className={styles.badgesSection}>
          <h3 className="label-caps mb-4">Accolade Shelf</h3>
          <div className={styles.badgesShelfGrid}>
            {BADGES_SHELF_TEMPLATES.map((badge, idx) => {
              const isEarned = getBadgeStatus(badge.name);
              return (
                <div 
                  key={idx} 
                  className={`${styles.badgeCard} blueprint-card ${isEarned ? styles.badgeEarned : styles.badgeLocked}`}
                >
                  <div className={styles.badgeIconWrapper}>
                    {isEarned ? (
                      <ShieldCheck size={28} className={styles.badgeIconActive} />
                    ) : (
                      <Lock size={20} className={styles.badgeIconLocked} />
                    )}
                  </div>
                  <div className={styles.badgeTextInfo}>
                    <h4 className={styles.badgeName}>{badge.name}</h4>
                    <p className={styles.badgeDesc}>{badge.description}</p>
                    <span className={`${styles.badgeStatusTag} utility-code`}>
                      {isEarned ? 'EARNED' : 'LOCKED'}
                    </span>
                  </div>
                </div>
              );
            })}
          </div>
        </section>

        {/* Submissions feed log */}
        <section className={styles.activitySection}>
          <div className={styles.activityHeader}>
            <span className="label-caps">Field Incident Reports Log</span>
            <span className={`${styles.reportsCountBadge} utility-code`}>
              {userIssues.length} Submissions
            </span>
          </div>

          <div className={styles.activityList}>
            {loading ? (
              <div className={styles.loader}>
                <span className="utility-code">Loading your reports...</span>
              </div>
            ) : userIssues.length > 0 ? (
              userIssues.map(issue => (
                <article key={issue.id} className={`${styles.issueCard} blueprint-card`}>
                  <div className={styles.issueHeader}>
                    <div>
                      <h4 className={styles.issueTitle}>{issue.title}</h4>
                      <p className={styles.issueDesc}>{issue.description}</p>
                    </div>
                    <span className={`${styles.refIdTag} utility-code text-outline`}>
                      REF #{issue.id?.slice(0, 8).toUpperCase()}
                    </span>
                  </div>
                  
                  <div className={styles.issueFooter}>
                    <div className={styles.metaRow}>
                      <span className="utility-code">{issue.category}</span>
                      <span className={styles.footerDivider}></span>
                      <span className="utility-code flex items-center gap-1">
                        <Calendar size={12} />
                        {new Date(issue.created_at).toLocaleDateString()}
                      </span>
                    </div>

                    <div className={styles.statusBadgeGroup}>
                      <span className={`${styles.statusBadge} ${
                        issue.status === 'resolved' ? styles.resolved : 
                        issue.status === 'in_progress' ? styles.inProgress : styles.reported
                      }`}>
                        {issue.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                  </div>
                </article>
              ))
            ) : (
              <div className={styles.noIssues}>
                <span className="utility-code">You haven't submitted any reports yet</span>
              </div>
            )}
          </div>
        </section>

      </div>
    </div>
  );
}
