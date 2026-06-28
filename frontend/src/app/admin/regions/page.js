// f:\CN Hackathon\frontend\src\app\admin\regions\page.js
'use client';

import React, { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';
import { Map, Plus, Pencil, Check, X, UserCog, RefreshCw, ChevronRight } from 'lucide-react';
import styles from './page.module.css';

export default function RegionManagementPage() {
  const { user } = useApp();
  const router = useRouter();

  const [regions, setRegions] = useState([]);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Create Region Form state (Super-admin only)
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [createForm, setCreateForm] = useState({ name: '', type: 'district', parent_region_id: '' });
  const [creating, setCreating] = useState(false);

  // Rename Region state
  const [editingRegionId, setEditingRegionId] = useState(null);
  const [editName, setEditName] = useState('');

  // Assign Admin state
  const [assignForm, setAssignForm] = useState({ user_id: '', admin_scope: 'district', region_id: '' });
  const [assigning, setAssigning] = useState(false);
  const [assignMsg, setAssignMsg] = useState('');

  // Determine roles
  const isSuperAdmin = !user?.admin_scope || user?.admin_scope === 'super';
  const isStateAdmin = user?.admin_scope === 'state';

  // Redirect district admins (no access at all)
  useEffect(() => {
    if (user && user.role === 'admin' && user.admin_scope === 'district') {
      router.replace('/admin');
    }
  }, [user, router]);

  const load = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const [regData, usrData] = await Promise.all([
        api.listRegions(),
        isSuperAdmin ? api.adminListUsers() : api.adminListUsers().catch(() => []) // Fallback in case of permissions
      ]);
      setRegions(regData);
      setUsers(usrData);
    } catch (e) {
      setError(e.message || 'Failed to load region data');
    } finally {
      setLoading(false);
    }
  }, [isSuperAdmin]);

  useEffect(() => {
    if (user) {
      load();
    }
  }, [load, user]);

  // All state-level regions (for "parent" dropdowns)
  const stateRegions = regions.filter(r => r.type === 'state');

  // Flatten regions for the assign-admin dropdown
  const allRegionsFlat = regions.flatMap(r => [
    { id: r.id, label: `${r.name} (state)`, type: 'state', parentId: null },
    ...(r.children || []).map(c => ({ id: c.id, label: `${c.name} (district)`, type: 'district', parentId: r.id }))
  ]);

  const handleCreate = async (e) => {
    e.preventDefault();
    if (!isSuperAdmin) return;
    setCreating(true);
    try {
      await api.createRegion({
        name: createForm.name,
        type: createForm.type,
        parent_region_id: createForm.parent_region_id || null,
      });
      setCreateForm({ name: '', type: 'district', parent_region_id: '' });
      setShowCreateForm(false);
      await load();
    } catch (e) {
      setError(e.message || 'Failed to create region');
    } finally {
      setCreating(false);
    }
  };

  const handleRename = async (regionId, regionType, parentRegionId) => {
    // Permission check:
    // - Super Admin can rename any region.
    // - State Admin can only rename districts within their own state.
    if (isStateAdmin) {
      if (regionType !== 'district' || parentRegionId !== user?.region_id) {
        setError('State admins can only rename districts within their own state.');
        setEditingRegionId(null);
        return;
      }
    }

    try {
      await api.updateRegion(regionId, { name: editName });
      setEditingRegionId(null);
      setEditName('');
      await load();
    } catch (e) {
      setError(e.message || 'Failed to rename region');
    }
  };

  const handleAssign = async (e) => {
    e.preventDefault();
    setAssigning(true);
    setAssignMsg('');
    try {
      // If State Admin, force admin_scope to 'district'
      const scopeToAssign = isStateAdmin ? 'district' : assignForm.admin_scope;
      await api.assignAdminRegion(assignForm.user_id, {
        admin_scope: scopeToAssign,
        region_id: assignForm.region_id || null,
      });
      setAssignMsg('Admin scope assigned successfully.');
      setAssignForm({ user_id: '', admin_scope: 'district', region_id: '' });
      await load();
    } catch (e) {
      setError(e.message || 'Failed to assign admin region');
    } finally {
      setAssigning(false);
    }
  };

  // Filter users that a State Admin is allowed to see/modify:
  // State Admins cannot promote/demote other State or Super admins.
  const assignableUsers = users.filter(u => {
    if (isSuperAdmin) return true;
    if (isStateAdmin) {
      // Can assign to citizens, or existing district admins in their own state.
      if (u.role === 'citizen') return true;
      if (u.admin_scope === 'district') {
        // Find if this district belongs to state admin's state
        const regionMatch = allRegionsFlat.find(r => r.id === u.region_id);
        return regionMatch && regionMatch.parentId === user?.region_id;
      }
    }
    return false;
  });

  return (
    <div className={styles.page}>
      {/* Header */}
      <header className={styles.pageHeader}>
        <div>
          <span className="label-caps" style={{ color: 'var(--ink-secondary)' }}>
            {isSuperAdmin ? 'SUPER-ADMIN CONSOLE' : 'STATE-ADMIN CONSOLE'}
          </span>
          <h1 className={styles.pageTitle}>
            <Map size={20} className={styles.titleIcon} />
            REGION MANAGEMENT
          </h1>
          <p className="utility-code" style={{ color: 'var(--ink-secondary)', marginTop: '4px' }}>
            {isSuperAdmin 
              ? 'Define state / district boundaries and assign admin jurisdiction'
              : 'View state boundaries and manage district admins under your jurisdiction'
            }
          </p>
        </div>
        <div className={styles.headerActions}>
          <button className="blueprint-btn blueprint-btn-secondary" onClick={load} disabled={loading}>
            <RefreshCw size={14} className={loading ? styles.spin : ''} />
            <span>REFRESH</span>
          </button>
          {isSuperAdmin && (
            <button className="blueprint-btn blueprint-btn-primary" onClick={() => setShowCreateForm(v => !v)}>
              <Plus size={14} />
              <span>NEW REGION</span>
            </button>
          )}
        </div>
      </header>

      {error && (
        <div className={styles.errorBanner}>
          <X size={14} style={{ cursor: 'pointer' }} onClick={() => setError('')} /> {error}
        </div>
      )}

      {/* Create Region Form (Super-admin only) */}
      {isSuperAdmin && showCreateForm && (
        <div className={`${styles.formCard} blueprint-card`}>
          <span className="label-caps">CREATE REGION</span>
          <form className={styles.form} onSubmit={handleCreate}>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className="utility-code">REGION NAME</label>
                <input
                  className={styles.input}
                  value={createForm.name}
                  onChange={e => setCreateForm(f => ({ ...f, name: e.target.value }))}
                  placeholder="e.g. Bengaluru Urban"
                  required
                />
              </div>
              <div className={styles.formGroup}>
                <label className="utility-code">TYPE</label>
                <select
                  className={styles.input}
                  value={createForm.type}
                  onChange={e => setCreateForm(f => ({ ...f, type: e.target.value, parent_region_id: '' }))}
                >
                  <option value="state">State</option>
                  <option value="district">District</option>
                </select>
              </div>
              {createForm.type === 'district' && (
                <div className={styles.formGroup}>
                  <label className="utility-code">PARENT STATE</label>
                  <select
                    className={styles.input}
                    value={createForm.parent_region_id}
                    onChange={e => setCreateForm(f => ({ ...f, parent_region_id: e.target.value }))}
                    required
                  >
                    <option value="">-- Select State --</option>
                    {stateRegions.map(r => (
                      <option key={r.id} value={r.id}>{r.name}</option>
                    ))}
                  </select>
                </div>
              )}
            </div>
            <div className={styles.formActions}>
              <button type="submit" className="blueprint-btn blueprint-btn-primary" disabled={creating}>
                {creating ? 'CREATING...' : 'CREATE'}
              </button>
              <button type="button" className="blueprint-btn blueprint-btn-secondary" onClick={() => setShowCreateForm(false)}>
                CANCEL
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Region Tree */}
      <section className={styles.section}>
        <div className={styles.sectionTitle}>
          <span className="label-caps">JURISDICTION HIERARCHY</span>
          <div className={styles.line} />
        </div>

        {loading ? (
          <div className="utility-code" style={{ padding: '24px', color: 'var(--ink-secondary)' }}>LOADING REGIONS...</div>
        ) : regions.length === 0 ? (
          <div className="blueprint-card" style={{ padding: '24px', textAlign: 'center' }}>
            <span className="utility-code">NO REGIONS CONFIGURED YET</span>
          </div>
        ) : (
          <div className={styles.regionList}>
            {regions.map(state => (
              <div key={state.id} className={`${styles.stateCard} blueprint-card`}>
                {/* State Row */}
                <div className={styles.regionRow}>
                  <div className={styles.regionMeta}>
                    <span className="label-caps" style={{ color: 'var(--signal-amber)' }}>STATE</span>
                    {editingRegionId === state.id ? (
                      <div className={styles.inlineEdit}>
                        <input
                          className={styles.input}
                          value={editName}
                          onChange={e => setEditName(e.target.value)}
                          autoFocus
                        />
                        <button className={styles.iconBtn} onClick={() => handleRename(state.id, 'state', null)} title="Save">
                          <Check size={14} />
                        </button>
                        <button className={styles.iconBtn} onClick={() => setEditingRegionId(null)} title="Cancel">
                          <X size={14} />
                        </button>
                      </div>
                    ) : (
                      <span className={styles.regionName}>{state.name}</span>
                    )}
                  </div>
                  {isSuperAdmin && (
                    <button
                      className={styles.iconBtn}
                      title="Rename"
                      onClick={() => { setEditingRegionId(state.id); setEditName(state.name); }}
                    >
                      <Pencil size={13} />
                    </button>
                  )}
                </div>

                {/* District Rows */}
                {(state.children || []).map(district => {
                  const canRenameDistrict = isSuperAdmin;
                  return (
                    <div key={district.id} className={styles.districtRow}>
                      <ChevronRight size={12} className={styles.chevron} />
                      <div className={styles.regionMeta}>
                        <span className="utility-code" style={{ color: 'var(--ink-secondary)', fontSize: '9px' }}>DISTRICT</span>
                        {editingRegionId === district.id ? (
                          <div className={styles.inlineEdit}>
                            <input
                              className={styles.input}
                              value={editName}
                              onChange={e => setEditName(e.target.value)}
                              autoFocus
                            />
                            <button className={styles.iconBtn} onClick={() => handleRename(district.id, 'district', state.id)} title="Save">
                              <Check size={14} />
                            </button>
                            <button className={styles.iconBtn} onClick={() => setEditingRegionId(null)} title="Cancel">
                              <X size={14} />
                            </button>
                          </div>
                        ) : (
                          <span className={styles.districtName}>{district.name}</span>
                        )}
                      </div>
                      {canRenameDistrict && (
                        <button
                          className={styles.iconBtn}
                          title="Rename"
                          onClick={() => { setEditingRegionId(district.id); setEditName(district.name); }}
                        >
                          <Pencil size={12} />
                        </button>
                      )}
                    </div>
                  );
                })}

                {(state.children || []).length === 0 && (
                  <p className="utility-code" style={{ padding: '8px 16px', color: 'var(--ink-secondary)', fontSize: '10px' }}>
                    NO DISTRICTS ATTACHED YET
                  </p>
                )}
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Assign Admin Region */}
      <section className={styles.section}>
        <div className={styles.sectionTitle}>
          <span className="label-caps">ASSIGN ADMIN JURISDICTION</span>
          <div className={styles.line} />
        </div>
        <div className={`${styles.formCard} blueprint-card`}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
            <UserCog size={16} style={{ color: 'var(--signal-amber)' }} />
            <span className="utility-code">
              {isSuperAdmin 
                ? 'Select a user and assign their administrative scope and region'
                : 'Select a user and assign them as a District Admin within your state'
              }
            </span>
          </div>
          <form className={styles.form} onSubmit={handleAssign}>
            <div className={styles.formRow}>
              <div className={styles.formGroup}>
                <label className="utility-code">USER</label>
                <select
                  className={styles.input}
                  value={assignForm.user_id}
                  onChange={e => setAssignForm(f => ({ ...f, user_id: e.target.value }))}
                  required
                >
                  <option value="">-- Select User --</option>
                  {assignableUsers.map(u => (
                    <option key={u.id} value={u.id}>
                      {u.name} ({u.email}) — {u.role === 'admin' ? `${u.admin_scope} admin` : u.role}
                    </option>
                  ))}
                </select>
              </div>
              {isSuperAdmin && (
                <div className={styles.formGroup}>
                  <label className="utility-code">SCOPE</label>
                  <select
                    className={styles.input}
                    value={assignForm.admin_scope}
                    onChange={e => setAssignForm(f => ({ ...f, admin_scope: e.target.value, region_id: '' }))}
                  >
                    <option value="district">District Admin</option>
                    <option value="state">State Admin</option>
                    <option value="super">Super Admin (Global)</option>
                  </select>
                </div>
              )}
              {assignForm.admin_scope !== 'super' && (
                <div className={styles.formGroup}>
                  <label className="utility-code">REGION</label>
                  <select
                    className={styles.input}
                    value={assignForm.region_id}
                    onChange={e => setAssignForm(f => ({ ...f, region_id: e.target.value }))}
                    required
                  >
                    <option value="">-- Select Region --</option>
                    {allRegionsFlat
                      .filter(r => {
                        if (isStateAdmin) {
                          // State Admins can only assign to districts within their own state
                          return r.type === 'district' && r.parentId === user?.region_id;
                        }
                        // Super Admin filters based on selected scope
                        if (assignForm.admin_scope === 'district') return r.type === 'district';
                        if (assignForm.admin_scope === 'state') return r.type === 'state';
                        return false;
                      })
                      .map(r => (
                        <option key={r.id} value={r.id}>{r.label}</option>
                      ))}
                  </select>
                </div>
              )}
            </div>
            <div className={styles.formActions}>
              <button type="submit" className="blueprint-btn blueprint-btn-primary" disabled={assigning}>
                {assigning ? 'ASSIGNING...' : 'ASSIGN JURISDICTION'}
              </button>
              {assignMsg && <span className="utility-code" style={{ color: '#4caf50' }}>{assignMsg}</span>}
            </div>
          </form>
        </div>
      </section>
    </div>
  );
}
