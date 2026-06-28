// f:\CN Hackathon\frontend\src\app\portal\page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';
import { 
  Plus, Search, Filter, ThumbsUp, CheckSquare, 
  MapPin, Clock, Tag, MessageSquare, AlertTriangle 
} from 'lucide-react';
import styles from './page.module.css';

export default function CitizenPortalPage() {
  const { user } = useApp();
  const router = useRouter();

  const [issues, setIssues] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('feed'); // 'feed' or 'my_reports'
  
  // Filters
  const [category, setCategory] = useState('');
  const [status, setStatus] = useState('');
  const [severity, setSeverity] = useState('');

  const loadIssues = useCallback(async () => {
    setLoading(true);
    try {
      const filters = {};
      if (category) filters.category = category;
      if (status) filters.status = status;
      if (severity) filters.severity = severity;
      
      const list = await api.listIssues(filters);
      setIssues(list.items || list || []);
    } catch (err) {
      console.error('Failed to load issues:', err);
      setIssues([]);
    } finally {

      setLoading(false);
    }
  }, [category, status, severity, user]);

  useEffect(() => {
    loadIssues();
  }, [loadIssues]);

  const handleUpvote = async (id, e) => {
    e.stopPropagation();
    e.preventDefault();
    try {
      await api.verifyIssue(id, 'upvote');
      loadIssues();
    } catch (err) {
      console.error('Failed to upvote/verify:', err);
      // Fallback local update for visual response
      setIssues(prev => prev.map(issue => 
        issue.id === id ? { ...issue, upvotes_count: issue.upvotes_count + 1 } : issue
      ));
    }
  };

  const handleVerify = async (id, e) => {
    e.stopPropagation();
    e.preventDefault();
    try {
      await api.verifyIssue(id, 'verify');
      loadIssues();
    } catch (err) {
      console.error('Failed to verify:', err);
      // Fallback local update
      setIssues(prev => prev.map(issue => 
        issue.id === id ? { ...issue, verifications_count: issue.verifications_count + 1 } : issue
      ));
    }
  };

  // Filter list based on active tab
  const displayedIssues = issues.filter(issue => {
    if (activeTab === 'my_reports') {
      return issue.reporter_id === user?.id;
    }
    return true;
  });

  const getStatusBadgeClass = (statusStr) => {
    switch (statusStr) {
      case 'resolved': return styles.statusResolved;
      case 'in_progress': return styles.statusProgress;
      default: return styles.statusReported;
    }
  };

  const getSeverityBadgeClass = (sevStr) => {
    switch (sevStr) {
      case 'critical': return styles.sevCritical;
      case 'high': return styles.sevHigh;
      case 'medium': return styles.sevMedium;
      default: return styles.sevLow;
    }
  };

  return (
    <div className={styles.portalWrapper}>
      <div className={styles.container}>
        
        {/* Header section */}
        <div className={styles.header}>
          <div>
            <span className="label-caps">CITIZEN DASHBOARD</span>
            <h1 className={styles.title}>Civic Action Feed</h1>
          </div>
          <Link href="/report" className="blueprint-btn blueprint-btn-primary">
            <Plus size={16} />
            <span>REPORT NEW ISSUE</span>
          </Link>
        </div>

        {/* Tab Selection */}
        <div className={styles.tabsContainer}>
          <button 
            className={`${styles.tabBtn} ${activeTab === 'feed' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('feed')}
          >
            GLOBAL FEED ({issues.length})
          </button>
          <button 
            className={`${styles.tabBtn} ${activeTab === 'my_reports' ? styles.tabActive : ''}`}
            onClick={() => setActiveTab('my_reports')}
          >
            MY REPORTS ({issues.filter(i => i.reporter_id === user?.id).length})
          </button>
        </div>

        {/* Filters Panel */}
        <div className={styles.filtersPanel}>
          <div className={styles.filterGroup}>
            <Filter size={14} className={styles.filterIcon} />
            <select 
              className={styles.filterSelect}
              value={category} 
              onChange={e => setCategory(e.target.value)}
            >
              <option value="">All Categories</option>
              <option value="Infrastructure">Infrastructure</option>
              <option value="Sanitation">Sanitation</option>
              <option value="Public Safety">Public Safety</option>
            </select>

            <select 
              className={styles.filterSelect}
              value={status} 
              onChange={e => setStatus(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="reported">Reported</option>
              <option value="in_progress">In Progress</option>
              <option value="resolved">Resolved</option>
            </select>

            <select 
              className={styles.filterSelect}
              value={severity} 
              onChange={e => setSeverity(e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="low">Low</option>
              <option value="medium">Medium</option>
              <option value="high">High</option>
              <option value="critical">Critical</option>
            </select>
          </div>
        </div>

        {/* Issues List */}
        {loading ? (
          <div className={styles.loader}>
            <span className="utility-code">Updating reports...</span>
          </div>
        ) : displayedIssues.length === 0 ? (
          <div className={styles.emptyFeed}>
            <AlertTriangle size={32} className={styles.emptyIcon} />
            <h3>No reports found</h3>
            <p className={styles.emptyText}>Adjust filters or register a new civic issue report in your district.</p>
          </div>
        ) : (
          <div className={styles.feedGrid}>
            {displayedIssues.map(issue => (
              <Link 
                href={`/issues/${issue.id}`} 
                key={issue.id} 
                className={`${styles.issueCard} blueprint-card blueprint-card-interactive`}
              >
                <div className={styles.cardHeader}>
                  <div className={styles.metaLeft}>
                    <div className={`${styles.statusBadge} ${getStatusBadgeClass(issue.status)}`}>
                      <span>{issue.status.replace('_', ' ').toUpperCase()}</span>
                    </div>
                    <div className={`${styles.severityBadge} ${getSeverityBadgeClass(issue.severity)}`}>
                      <span>{issue.severity.toUpperCase()}</span>
                    </div>
                  </div>
                  <span className="utility-code text-outline">{issue.id}</span>
                </div>

                <div className={styles.cardBody}>
                  <h3 className={styles.issueTitle}>{issue.title}</h3>
                  <p className={styles.issueDesc}>{issue.description}</p>
                </div>

                <div className={styles.cardFooter}>
                  <div className={styles.metaRow}>
                    <div className={styles.metaItem}>
                      <Tag size={14} />
                      <span>{issue.category}</span>
                    </div>
                    <div className={styles.metaItem}>
                      <MapPin size={14} />
                      <span>{issue.latitude?.toFixed(4)}, {issue.longitude?.toFixed(4)}</span>
                    </div>
                    <div className={styles.metaItem}>
                      <Clock size={14} />
                      <span>{new Date(issue.created_at).toLocaleDateString()}</span>
                    </div>
                  </div>

                  <div className={styles.actionRow}>
                    {/* Upvote */}
                    <button 
                      className={`${styles.actionBtn} ${styles.upvoteBtn}`} 
                      onClick={(e) => handleUpvote(issue.id, e)}
                      title="Upvote issue significance"
                    >
                      <ThumbsUp size={14} />
                      <span>{issue.upvotes_count || 0}</span>
                    </button>
                    {/* Verify */}
                    <button 
                      className={`${styles.actionBtn} ${styles.verifyBtn}`} 
                      onClick={(e) => handleVerify(issue.id, e)}
                      title="Verify issue presence"
                    >
                      <CheckSquare size={14} />
                      <span>{issue.verifications_count || 0}</span>
                    </button>
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}

      </div>
    </div>
  );
}
