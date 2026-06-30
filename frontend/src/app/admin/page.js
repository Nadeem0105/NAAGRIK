// f:\CN Hackathon\frontend\src\app\admin\page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';
import { 
  ShieldAlert, RefreshCw, AlertTriangle, Upload, Clock, CheckCircle2 
} from 'lucide-react';
import styles from './page.module.css';

export default function ManageIssuesPage() {
  const { user } = useApp();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Data States
  const [issues, setIssues] = useState([]);
  const [departments, setDepartments] = useState([]);

  // Checkbox state for multi-selection
  const [selectedIssueIds, setSelectedIssueIds] = useState([]);

  // Bulk Operations State
  const [bulkStatus, setBulkStatus] = useState('');
  const [bulkSeverity, setBulkSeverity] = useState('');
  const [bulkDeptId, setBulkDeptId] = useState('');
  const [bulkSlaDue, setBulkSlaDue] = useState('');
  
  // Resolution Proof Upload
  const [uploadingProof, setUploadingProof] = useState(false);
  const [uploadedProofUrl, setUploadedProofUrl] = useState('');
  const [dragActive, setDragActive] = useState(false);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const issuesRes = await api.adminListIssues({ limit: 100 });
      setIssues(issuesRes.items || issuesRes || []);

      const deptsRes = await api.getDepartments();
      setDepartments(deptsRes || []);
    } catch (err) {
      console.error('Failed to load admin issues data:', err);
      setError(err.message || 'Failed to load issues. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadData();
  }, [loadData]);

  // Handle single check
  const handleSelectIssue = (id) => {
    setSelectedIssueIds(prev => 
      prev.includes(id) ? prev.filter(item => item !== id) : [...prev, id]
    );
  };

  // Handle select all
  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedIssueIds(issues.map(i => i.id));
    } else {
      setSelectedIssueIds([]);
    }
  };

  // Drag & Drop Upload
  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      await handleUploadFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileChange = async (e) => {
    if (e.target.files && e.target.files[0]) {
      await handleUploadFile(e.target.files[0]);
    }
  };

  const handleUploadFile = async (file) => {
    setUploadingProof(true);
    setError('');
    try {
      const formData = new FormData();
      formData.append('file', file);
      
      const res = await api.adminUploadProof(formData);
      setUploadedProofUrl(res.url);
    } catch (err) {
      console.error('File upload failed:', err);
      setError(err.message || 'Resolution proof upload failed.');
      // Local fallback placeholder
      setUploadedProofUrl('https://picsum.photos/800/600?random=resolution');
    } finally {
      setUploadingProof(false);
    }
  };

  // Bulk Apply updates
  const handleBulkUpdate = async (e) => {
    e.preventDefault();
    if (selectedIssueIds.length === 0) return;

    setLoading(true);
    try {
      const payload = {};
      if (bulkStatus) payload.status = bulkStatus;
      if (bulkSeverity) payload.severity = bulkSeverity;
      if (bulkDeptId) payload.assigned_department_id = bulkDeptId === 'unassigned' ? null : bulkDeptId;
      if (bulkSlaDue) payload.sla_due_at = new Date(bulkSlaDue).toISOString();
      if (bulkStatus === 'resolved' && uploadedProofUrl) {
        payload.resolution_image_url = uploadedProofUrl;
      }

      // Loop through all selected and patch
      await Promise.all(
        selectedIssueIds.map(id => api.adminUpdateIssue(id, payload))
      );

      // Reset state
      setSelectedIssueIds([]);
      setBulkStatus('');
      setBulkSeverity('');
      setBulkDeptId('');
      setBulkSlaDue('');
      setUploadedProofUrl('');
      
      loadData();
    } catch (err) {
      console.error('Failed to apply bulk updates:', err);
      setError('Bulk update failed. Some issues may not have been updated.');
      loadData();
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={styles.issuesPageContainer}>
      {/* Top Status Header */}
      <header className={`${styles.pageHeader} animate-fade-in-up`}>
        <div>
          <span className="label-caps text-outline">OPERATIONS PORTAL</span>
          <h2 className={styles.pageTitle}>Issue Operations Console</h2>
        </div>
        <div className={styles.systemStatus}>
          <button className="blueprint-btn blueprint-btn-secondary mr-4" onClick={loadData} disabled={loading}>
            <RefreshCw size={14} className={loading ? styles.spinner : ''} />
            <span>REFRESH</span>
          </button>
          <span className="utility-code text-success-green flex items-center gap-2">
            <span className={styles.statusPulseDot}></span> OPERATIONAL
          </span>
        </div>
      </header>

      {error && (
        <div className={`${styles.errorAlert} animate-scale-up`}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className={styles.issuesLayout}>
        {/* Table and list of issues */}
        <div className={`${styles.tableCard} blueprint-card animate-fade-in-up delay-100`}>
          <div className={styles.tableResponsive}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>
                    <input 
                      type="checkbox" 
                      onChange={handleSelectAll}
                      checked={selectedIssueIds.length === issues.length && issues.length > 0} 
                    />
                  </th>
                  <th className="label-caps">ID</th>
                  <th className="label-caps">INCIDENT TITLE</th>
                  <th className="label-caps">SEVERITY</th>
                  <th className="label-caps">ASSIGNED DEPARTMENT</th>
                  <th className="label-caps">STATUS</th>
                </tr>
              </thead>
              <tbody>
                {issues.map((issue, index) => (
                  <tr 
                    key={issue.id} 
                    className={selectedIssueIds.includes(issue.id) ? styles.rowSelected : ''}
                  >
                    <td>
                      <input 
                        type="checkbox" 
                        checked={selectedIssueIds.includes(issue.id)}
                        onChange={() => handleSelectIssue(issue.id)}
                      />
                    </td>
                    <td className="utility-code">{issue.id?.slice(0, 6).toUpperCase()}</td>
                    <td>
                      <div className={styles.issueTableTitle}>{issue.title}</div>
                      <div className={`${styles.issueTableCat} utility-code`}>{issue.category}</div>
                    </td>
                    <td>
                      <span className={`${styles.tableSeverity} ${issue.severity === 'high' ? styles.sevHigh : ''}`}>
                        {issue.severity?.toUpperCase() || 'MEDIUM'}
                      </span>
                    </td>
                    <td>
                      <span className="utility-code">{issue.assigned_department_name || 'Unassigned'}</span>
                    </td>
                    <td>
                      <span className={`${styles.tableStatus} ${
                        issue.status === 'resolved' ? styles.statResolved : 
                        issue.status === 'in_progress' ? styles.statProgress : styles.statReported
                      }`}>
                        {issue.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </td>
                  </tr>
                ))}

                {issues.length === 0 && !loading && (
                  <tr>
                    <td colSpan="6" className="text-center py-8">
                      <span className="utility-code">No issues reported yet</span>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>

        {/* Bulk Action Pane / Sidebar */}
        {selectedIssueIds.length > 0 && (
          <div className={`${styles.bulkPane} blueprint-card animate-slide-in-right`}>
            <div className={styles.bulkHeader}>
              <span className="label-caps">Bulk Operations ({selectedIssueIds.length} Selected)</span>
              <div className={styles.line}></div>
            </div>

            <form onSubmit={handleBulkUpdate} className={styles.bulkForm}>
              
              {/* Status update selector */}
              <div className={styles.formGroup}>
                <label className="label-caps">Update Status</label>
                <select 
                  value={bulkStatus} 
                  onChange={e => setBulkStatus(e.target.value)}
                  className={styles.formSelect}
                >
                  <option value="">No Change</option>
                  <option value="reported">Reported</option>
                  <option value="verified">Verified</option>
                  <option value="assigned">Assigned</option>
                  <option value="in_progress">In Progress</option>
                  <option value="resolved">Resolved</option>
                </select>
              </div>

              {/* Reassignment department selector */}
              <div className={styles.formGroup}>
                <label className="label-caps">Reassign Department</label>
                <select 
                  value={bulkDeptId} 
                  onChange={e => setBulkDeptId(e.target.value)}
                  className={styles.formSelect}
                >
                  <option value="">No Change</option>
                  <option value="unassigned">Unassign</option>
                  {departments.map(d => (
                    <option key={d.id} value={d.id}>{d.name}</option>
                  ))}
                </select>
              </div>

              {/* Severity level selector */}
              <div className={styles.formGroup}>
                <label className="label-caps">Change Severity</label>
                <select 
                  value={bulkSeverity} 
                  onChange={e => setBulkSeverity(e.target.value)}
                  className={styles.formSelect}
                >
                  <option value="">No Change</option>
                  <option value="low">Low</option>
                  <option value="medium">Medium</option>
                  <option value="high">High</option>
                </select>
              </div>

              {/* SLA Target Due Date picker */}
              <div className={styles.formGroup}>
                <label className="label-caps">SLA Target Due Date</label>
                <input 
                  type="datetime-local" 
                  value={bulkSlaDue}
                  onChange={e => setBulkSlaDue(e.target.value)}
                  className={styles.formInput}
                />
              </div>

              {/* Resolution Proof Dropzone (visible only if resolving) */}
              {bulkStatus === 'resolved' && (
                <div className={styles.formGroup}>
                  <label className="label-caps">Resolution Proof</label>
                  <div 
                    className={`${styles.dropzone} ${dragActive ? styles.dropzoneActive : ''} ${uploadedProofUrl ? styles.dropzoneCompleted : ''}`}
                    onDragEnter={handleDrag}
                    onDragLeave={handleDrag}
                    onDragOver={handleDrag}
                    onDrop={handleDrop}
                  >
                    <input 
                      type="file" 
                      id="file-upload" 
                      className={styles.fileInput} 
                      onChange={handleFileChange}
                      accept="image/*"
                    />
                    <label htmlFor="file-upload" className={styles.dropzoneLabel}>
                      {uploadingProof ? (
                        <Clock className={styles.spinner} />
                      ) : uploadedProofUrl ? (
                        <CheckCircle2 className={styles.dropzoneSuccessIcon} />
                      ) : (
                        <Upload />
                      )}
                      <span className="utility-code mt-2">
                        {uploadingProof ? 'UPLOADING PROOF...' : 
                         uploadedProofUrl ? 'PROOF UPLOADED' : 'DRAG & DROP IMAGE'}
                      </span>
                    </label>
                  </div>
                </div>
              )}

              <button type="submit" className="blueprint-btn blueprint-btn-primary w-full mt-4" disabled={loading}>
                <span>APPLY BULK UPDATES</span>
              </button>
            </form>
          </div>
        )}
      </div>
    </div>
  );
}
