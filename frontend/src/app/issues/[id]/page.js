// f:\CN Hackathon\frontend\src\app\issues\[id]\page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { api } from '@/services/api';
import { useApp } from '@/context/AppContext';
import { 
  ArrowLeft, MessageSquare, ThumbsUp, CheckSquare, 
  MapPin, Clock, Shield, Tag, User, Send, Bell, BellOff,
  AlertTriangle, CheckCircle2 
} from 'lucide-react';
import styles from './page.module.css';

export default function IssueDetailPage({ params }) {
  const router = useRouter();
  const { user } = useApp();
  const unwrappedParams = React.use(params);
  const id = unwrappedParams.id;

  const [issue, setIssue] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(true);
  const [submittingComment, setSubmittingComment] = useState(false);
  const [submittingFollow, setSubmittingFollow] = useState(false);
  const [error, setError] = useState('');
  const [timeLeft, setTimeLeft] = useState('');

  const loadData = useCallback(async () => {
    try {
      const data = await api.getIssue(id);
      setIssue(data);

      try {
        const commData = await api.getComments(id);
        setComments(commData.items || commData || []);
      } catch (commErr) {
        console.error('Failed to load comments:', commErr);
      }
    } catch (err) {
      console.error('Failed to load issue details:', err);
      setError(err.message || 'Failed to load issue details. Please try again.');
      setIssue(null);
      setComments([]);
    } finally {
      setLoading(false);
    }
  }, [id]);

  useEffect(() => {
    if (id) {
      loadData();
    }
  }, [id, loadData]);

  // SLA Countdown Timer
  useEffect(() => {
    if (!issue) return;

    const calculateTimeLeft = () => {
      // Use due date if provided, otherwise default to 3 days after creation date
      const dueTime = issue.sla_due_at 
        ? new Date(issue.sla_due_at).getTime()
        : new Date(issue.created_at).getTime() + (3 * 24 * 60 * 60 * 1000);
      
      const now = new Date().getTime();
      const diff = dueTime - now;

      if (issue.status === 'resolved') {
        setTimeLeft('RESOLVED');
        return;
      }

      if (diff <= 0) {
        setTimeLeft('SLA BREACHED');
        return;
      }

      const days = Math.floor(diff / (1000 * 60 * 60 * 24));
      const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      const dStr = days > 0 ? `${days}d ` : '';
      const hStr = String(hours).padStart(2, '0');
      const mStr = String(minutes).padStart(2, '0');
      const sStr = String(seconds).padStart(2, '0');

      setTimeLeft(`${dStr}${hStr}:${mStr}:${sStr}`);
    };

    calculateTimeLeft();
    const interval = setInterval(calculateTimeLeft, 1000);
    return () => clearInterval(interval);
  }, [issue]);

  const handleUpvote = async () => {
    try {
      await api.verifyIssue(id, 'upvote');
      loadData();
    } catch (err) {
      console.error('Failed to upvote:', err);
      setIssue(prev => ({ ...prev, upvotes_count: (prev.upvotes_count || 0) + 1 }));
    }
  };

  const handleVerify = async () => {
    try {
      await api.verifyIssue(id, 'verify');
      loadData();
    } catch (err) {
      console.error('Failed to verify:', err);
      setIssue(prev => ({ ...prev, verifications_count: (prev.verifications_count || 0) + 1 }));
    }
  };

  const handleFollowToggle = async () => {
    if (!user) {
      router.push('/login');
      return;
    }
    setSubmittingFollow(true);
    try {
      if (issue.is_followed) {
        await api.unfollowIssue(id);
      } else {
        await api.followIssue(id);
      }
      loadData();
    } catch (err) {
      console.error('Failed to toggle follow status:', err);
    } finally {
      setSubmittingFollow(false);
    }
  };

  const handlePostComment = async (e) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setSubmittingComment(true);
    try {
      await api.createComment(id, newComment);
      setNewComment('');
      loadData();
    } catch (err) {
      console.error('Failed to post comment:', err);
      // Local fallback insert
      setComments(prev => [
        ...prev,
        {
          id: String(Date.now()),
          user_name: user?.name || "You",
          content: newComment,
          created_at: new Date().toISOString()
        }
      ]);
      setNewComment('');
    } finally {
      setSubmittingComment(false);
    }
  };

  if (loading) {
    return (
      <div className={styles.detailWrapper}>
        <div className={styles.loader}>
          <span className="utility-code">Loading issue details...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.detailWrapper}>
      <div className={styles.container}>
        
        {/* Back Link & Follow Row */}
        <div className={styles.topActionRow}>
          <Link href="/portal" className={styles.backLink}>
            <ArrowLeft size={16} />
            <span className="label-caps">Back to Portal</span>
          </Link>

          {issue && (
            <button 
              onClick={handleFollowToggle}
              disabled={submittingFollow}
              className={`${styles.followBtn} blueprint-btn ${issue.is_followed ? 'blueprint-btn-secondary' : 'blueprint-btn-primary'}`}
            >
              {issue.is_followed ? (
                <>
                  <BellOff size={14} />
                  <span>UNFOLLOW UPDATES</span>
                </>
              ) : (
                <>
                  <Bell size={14} />
                  <span>FOLLOW UPDATES</span>
                </>
              )}
            </button>
          )}
        </div>

        {error && !issue ? (
          <div className={styles.errorContainer}>
            <h3 className="label-caps">REPORT LOG CORRUPT</h3>
            <p className="utility-code">{error}</p>
          </div>
        ) : (
          <div className={styles.contentLayout}>
            
            {/* LEFT COLUMN: Main Issue Details */}
            <div className={styles.mainCol}>
              
              {/* Header block */}
              <header className={styles.issueHeader}>
                <div className={styles.headerMeta}>
                  <div className={`${styles.statusBadge} ${
                    issue.status === 'resolved' ? styles.statusResolved : 
                    issue.status === 'in_progress' ? styles.statusProgress : styles.statusReported
                  }`}>
                    <span>{issue.status.replace('_', ' ').toUpperCase()}</span>
                  </div>
                  <span className="utility-code text-outline">REF #{issue.id?.slice(0, 8).toUpperCase()}</span>
                </div>
                <h1 className={styles.title}>{issue.title}</h1>
                <p className={styles.description}>{issue.description}</p>
              </header>

              {/* Before/After Visual Evidence Section */}
              <section className={styles.evidenceSection}>
                <div className={styles.sectionHeader}>
                  <span className="label-caps">Visual Audit Evidence</span>
                  <div className={styles.line}></div>
                </div>

                <div className={styles.comparisonGrid}>
                  
                  {/* Before / Reported Condition */}
                  <div className={styles.comparisonCard}>
                    <div className={styles.comparisonLabel}>
                      <span className="label-caps">BEFORE: Reported Condition</span>
                    </div>
                    <div className={styles.imageContainer}>
                      {issue.image_urls && issue.image_urls.length > 0 ? (
                        <img src={issue.image_urls[0]} alt="Reported condition" className={styles.evidenceImage} />
                      ) : (
                        <div className={styles.noImagePlaceholder}>
                          <AlertTriangle size={24} />
                          <span className="utility-code">No photo provided</span>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* After / Resolution Proof */}
                  <div className={styles.comparisonCard}>
                    <div className={styles.comparisonLabel}>
                      <span className="label-caps">AFTER: Resolution Proof</span>
                    </div>
                    <div className={styles.imageContainer}>
                      {issue.status === 'resolved' && issue.resolution_image_url ? (
                        <img src={issue.resolution_image_url} alt="Resolution proof" className={styles.evidenceImage} />
                      ) : issue.status === 'resolved' ? (
                        <div className={styles.resolvedNoImagePlaceholder}>
                          <CheckCircle2 size={24} className={styles.resolvedIcon} />
                          <span className="utility-code">RESOLVED</span>
                          <span className={styles.placeholderSubText}>No resolution photo uploaded by municipal crew.</span>
                        </div>
                      ) : (
                        <div className={styles.pendingPlaceholder}>
                          <Clock size={24} className={styles.pendingIcon} />
                          <span className="utility-code">Resolution pending</span>
                          <span className={styles.placeholderSubText}>Awaiting municipal dispatch resolution proof.</span>
                        </div>
                      )}
                    </div>
                  </div>

                </div>
              </section>

              {/* Geolocation Log */}
              <section className={styles.locationSection}>
                <div className={styles.sectionHeader}>
                  <span className="label-caps">Geolocation Log</span>
                  <div className={styles.line}></div>
                </div>
                <div className={styles.locationCard}>
                  <MapPin size={18} className={styles.locationPinIcon} />
                  <div className={styles.locationInfo}>
                    <span className={styles.locationCategory}>{issue.category}</span>
                    <span className="utility-code text-outline">
                      LAT: {issue.latitude?.toFixed(5)}° N, LNG: {issue.longitude?.toFixed(5)}° E
                    </span>
                  </div>
                </div>
              </section>

              {/* Citizen Endorsement & Verification Actions */}
              <section className={styles.actionsSection}>
                <button className={`${styles.actionButton} blueprint-btn`} onClick={handleUpvote}>
                  <ThumbsUp size={16} />
                  <span>ENDORSE REPORT ({issue.upvotes_count || 0})</span>
                </button>
                <button className={`${styles.actionButton} blueprint-btn`} onClick={handleVerify}>
                  <CheckSquare size={16} />
                  <span>STILL PRESENT ({issue.verifications_count || 0})</span>
                </button>
              </section>

              {/* Field Notes / Comments Thread */}
              <section className={styles.commentsSection}>
                <div className={styles.sectionHeader}>
                  <span className="label-caps">Field Notes Discussion ({comments.length})</span>
                  <div className={styles.line}></div>
                </div>

                <div className={styles.commentList}>
                  {comments.map(c => (
                    <div key={c.id} className={styles.commentCard}>
                      <div className={styles.commentAvatar}>
                        <User size={16} />
                      </div>
                      <div className={styles.commentBody}>
                        <div className={styles.commentMeta}>
                          <span className={styles.commentUser}>{c.user_name || 'Citizen'}</span>
                          <span className="utility-code">{new Date(c.created_at).toLocaleString()}</span>
                        </div>
                        <p className={styles.commentText}>{c.content}</p>
                      </div>
                    </div>
                  ))}

                  {comments.length === 0 && (
                    <div className={styles.emptyComments}>
                      <span className="utility-code">No comments or updates yet</span>
                    </div>
                  )}

                  {/* Add Field Note Comment Form */}
                  <form onSubmit={handlePostComment} className={styles.commentForm}>
                    <textarea
                      placeholder="Add local updates or follow-up details on this incident..."
                      value={newComment}
                      onChange={e => setNewComment(e.target.value)}
                      required
                      rows={3}
                      className={styles.commentTextarea}
                    ></textarea>
                    <div className={styles.commentSubmitRow}>
                      <button 
                        type="submit" 
                        disabled={submittingComment} 
                        className="blueprint-btn blueprint-btn-primary"
                      >
                        <span>{submittingComment ? 'SUBMITTING...' : 'ADD COMMENT'}</span>
                        <Send size={14} />
                      </button>
                    </div>
                  </form>
                </div>
              </section>

            </div>

            {/* RIGHT COLUMN: SLA & Stepper Status */}
            <div className={styles.sideCol}>
              
              {/* SLA countdown clock */}
              <div className={`${styles.sideCard} blueprint-card`}>
                <span className="label-caps mb-2 block">Resolution Timer</span>
                <div className={`${styles.slaClock} utility-code ${timeLeft === 'SLA BREACHED' ? styles.slaBreached : ''}`}>
                  {timeLeft}
                </div>
                <p className={styles.slaSub}>Target turnaround time for {issue.category} classifications.</p>
              </div>

              {/* Status Timeline lifecycle */}
              <div className={`${styles.sideCard} blueprint-card`}>
                <span className="label-caps mb-4 block">Status Timeline</span>
                <div className={styles.timeline}>
                  
                  {/* Step 3: Resolved */}
                  <div className={`${styles.timelineStep} ${
                    issue.status === 'resolved' ? styles.stepCurrent : styles.stepInactive
                  }`}>
                    <div className={styles.timelineDot}></div>
                    <div className={styles.stepInfo}>
                      <span className="label-caps">RESOLVED</span>
                      <p className="utility-code">Incident cleared & verified</p>
                    </div>
                  </div>

                  {/* Step 2: In Progress */}
                  <div className={`${styles.timelineStep} ${
                    issue.status === 'in_progress' ? styles.stepCurrent : 
                    issue.status === 'resolved' ? styles.stepCompleted : styles.stepInactive
                  }`}>
                    <div className={styles.timelineDot}></div>
                    <div className={styles.stepInfo}>
                      <span className="label-caps">IN PROGRESS</span>
                      <p className="utility-code">Dispatched municipal team</p>
                    </div>
                  </div>

                  {/* Step 1: Reported */}
                  <div className={`${styles.timelineStep} ${
                    issue.status === 'reported' ? styles.stepCurrent : styles.stepCompleted
                  }`}>
                    <div className={styles.timelineDot}></div>
                    <div className={styles.stepInfo}>
                      <span className="label-caps">REPORTED</span>
                      <p className="utility-code">Issue report received</p>
                    </div>
                  </div>

                </div>
              </div>

            </div>

          </div>
        )}

      </div>
    </div>
  );
}
