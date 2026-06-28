// f:\CN Hackathon\frontend\src\app\admin\departments\page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import { Plus, AlertTriangle, RefreshCw } from 'lucide-react';
import styles from '../page.module.css';
import { useApp } from '@/context/AppContext';

export default function DepartmentsPage() {
  const { user } = useApp();
  const [departments, setDepartments] = useState([]);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Create Department form state
  const [newDeptName, setNewDeptName] = useState('');
  const [newDeptCategories, setNewDeptCategories] = useState('');
  const [selectedRegionId, setSelectedRegionId] = useState('');

  const loadDepartments = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.getDepartments();
      setDepartments(data || []);
    } catch (err) {
      console.error('Failed to load departments:', err);
      setError(err.message || 'Failed to load departments. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  const loadRegions = useCallback(async () => {
    if (!user || user.admin_scope === 'district') return;
    try {
      const data = await api.listRegions();
      // Filter regions based on scope
      if (user.admin_scope === 'state') {
        // State Admin: only see their own state and districts under their state
        const filtered = (data || []).filter(r => 
          r.id === user.region_id || r.parent_region_id === user.region_id
        );
        setRegions(filtered);
        // Pre-select their own state region
        if (filtered.length > 0) {
          setSelectedRegionId(user.region_id || filtered[0].id);
        }
      } else {
        // Super Admin: see all regions
        setRegions(data || []);
      }
    } catch (err) {
      console.error('Failed to load regions:', err);
    }
  }, [user]);

  useEffect(() => {
    loadDepartments();
    loadRegions();
  }, [loadDepartments, loadRegions]);

  const handleCreateDept = async (e) => {
    e.preventDefault();
    if (!newDeptName) return;

    setError('');
    try {
      const cats = newDeptCategories.split(',').map(s => s.trim().toLowerCase()).filter(Boolean);
      const regionVal = selectedRegionId || null;
      await api.createDepartment(newDeptName, cats, regionVal);
      setNewDeptName('');
      setNewDeptCategories('');
      loadDepartments();
    } catch (err) {
      console.error('Failed to create department:', err);
      setError(err.message || 'Failed to register department.');
    }
  };

  const isDistrictAdmin = user?.admin_scope === 'district';

  return (
    <div>
      {/* Top Status Header */}
      <header className={styles.pageHeader}>
        <div>
          <span className="label-caps text-outline">DEPARTMENT OPERATIONS</span>
          <h2 className={styles.pageTitle}>Municipal Departments</h2>
        </div>
        <div className={styles.systemStatus}>
          <button className="blueprint-btn blueprint-btn-secondary mr-4" onClick={loadDepartments} disabled={loading}>
            <RefreshCw size={14} className={loading ? styles.spinner : ''} />
            <span>REFRESH</span>
          </button>
          <span className="utility-code text-success-green flex items-center gap-2">
            <span className={styles.statusPulseDot}></span> MONITOR ON
          </span>
        </div>
      </header>

      {error && (
        <div className={styles.errorAlert} style={{ marginTop: '24px' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className={styles.dashGrid} style={{ marginTop: '24px' }}>
        
        {/* Left Side: Active Departments List */}
        <div className={isDistrictAdmin ? 'w-full' : styles.criticalCol}>
          <span className="label-caps mb-4 block">ACTIVE DEPARTMENTS</span>
          <div className={styles.criticalList}>
            {departments.map(d => (
              <div key={d.id} className={`${styles.criticalItem} blueprint-card`}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <h4 className={styles.criticalTitle}>{d.name}</h4>
                  {d.region_name && (
                    <span className="utility-code text-outline" style={{ fontSize: '11px' }}>
                      📍 {d.region_name}
                    </span>
                  )}
                </div>
                <div className={styles.catMappings} style={{ marginTop: '8px' }}>
                  {d.category_mapping && d.category_mapping.map((cat, i) => (
                    <span key={i} className={`${styles.catMappingBadge} utility-code`}>
                      {cat}
                    </span>
                  ))}
                  {(!d.category_mapping || d.category_mapping.length === 0) && (
                    <span className="utility-code text-outline text-xs">No category mapping</span>
                  )}
                </div>
              </div>
            ))}

            {departments.length === 0 && !loading && (
              <div className="blueprint-card p-6 text-center">
                <span className="utility-code">No departments created yet</span>
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Register New Department Form (Hidden for District Admins) */}
        {!isDistrictAdmin && (
          <div className={styles.mapCol}>
            <div className={`${styles.sideCard} blueprint-card`}>
              <span className="label-caps mb-4 block">REGISTER NEW DEPARTMENT</span>
              <form onSubmit={handleCreateDept} className={styles.deptForm}>
                <div className={styles.formGroup}>
                  <label className="label-caps">DEPARTMENT NAME</label>
                  <input 
                    type="text" 
                    placeholder="e.g. Department of Public Works" 
                    value={newDeptName}
                    onChange={e => setNewDeptName(e.target.value)}
                    required
                    className={styles.formInput}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label className="label-caps">MAPPED CATEGORIES (COMMA SEPARATED)</label>
                  <input 
                    type="text" 
                    placeholder="e.g. water_leak, sewage, trash" 
                    value={newDeptCategories}
                    onChange={e => setNewDeptCategories(e.target.value)}
                    className={styles.formInput}
                  />
                </div>
                <div className={styles.formGroup}>
                  <label className="label-caps">JURISDICTION / REGION</label>
                  <select
                    value={selectedRegionId}
                    onChange={e => setSelectedRegionId(e.target.value)}
                    className={styles.formInput}
                    style={{ backgroundColor: 'var(--paper-bright)', color: 'var(--ink)' }}
                  >
                    {user?.admin_scope === 'super' && (
                      <option value="">Global / All Regions</option>
                    )}
                    {regions.map(r => (
                      <option key={r.id} value={r.id}>
                        {r.name} ({r.type})
                      </option>
                    ))}
                  </select>
                </div>
                <button type="submit" className="blueprint-btn blueprint-btn-primary w-full" style={{ marginTop: '16px' }}>
                  <Plus size={16} />
                  <span>CREATE DEPARTMENT</span>
                </button>
              </form>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
