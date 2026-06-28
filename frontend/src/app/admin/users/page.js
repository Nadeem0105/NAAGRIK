// f:\CN Hackathon\frontend\src\app\admin\users\page.js
'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import { Shield, AlertTriangle, RefreshCw } from 'lucide-react';
import styles from '../page.module.css';
import { useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';

export default function UserDirectoryPage() {
  const router = useRouter();
  const { user, loading: userLoading } = useApp();
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (!userLoading) {
      const isSuperAdmin = user?.role === 'admin' && (!user?.admin_scope || user?.admin_scope === 'super');
      if (!isSuperAdmin) {
        router.replace('/admin');
      }
    }
  }, [user, userLoading, router]);

  const loadUsers = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const data = await api.adminListUsers();
      setUsers(data || []);
    } catch (err) {
      console.error('Failed to load user directory:', err);
      setError(err.message || 'Failed to load users. Please try again.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (user && (user.role === 'admin' && (!user.admin_scope || user.admin_scope === 'super'))) {
      loadUsers();
    }
  }, [user, loadUsers]);

  if (userLoading || !user || user.role !== 'admin' || (user.admin_scope && user.admin_scope !== 'super')) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '80vh' }}>
        <div className="utility-code">Verifying authorization...</div>
      </div>
    );
  }

  const handleToggleRole = async (userId, currentRole) => {
    const nextRole = currentRole === 'admin' ? 'citizen' : 'admin';
    try {
      await api.adminUpdateUserRole(userId, nextRole);
      loadUsers();
    } catch (err) {
      console.error('Failed to update user role:', err);
      setError(err.message || 'Failed to update user role.');
    }
  };

  return (
    <div>
      {/* Top Status Header */}
      <header className={styles.pageHeader}>
        <div>
          <span className="label-caps text-outline">USER DIRECTORY DATABASE</span>
          <h2 className={styles.pageTitle}>Authority Directory Console</h2>
        </div>
        <div className={styles.systemStatus}>
          <button className="blueprint-btn blueprint-btn-secondary mr-4" onClick={loadUsers} disabled={loading}>
            <RefreshCw size={14} className={loading ? styles.spinner : ''} />
            <span>REFRESH</span>
          </button>
          <span className="utility-code text-success-green flex items-center gap-2">
            <span className={styles.statusPulseDot}></span> SYSTEM ON
          </span>
        </div>
      </header>

      {error && (
        <div className={styles.errorAlert} style={{ marginTop: '24px' }}>
          <AlertTriangle size={16} />
          <span>{error}</span>
        </div>
      )}

      <div className={`${styles.tableCard} blueprint-card`} style={{ marginTop: '24px' }}>
        <div className={styles.tableResponsive}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th className="label-caps">CITIZEN NAME</th>
                <th className="label-caps">EMAIL</th>
                <th className="label-caps">MEMBER ROLE</th>
                <th className="label-caps">IMPACT SCORE</th>
                <th className="label-caps">ACTIONS</th>
              </tr>
            </thead>
            <tbody>
              {users.map(u => (
                <tr key={u.id}>
                  <td className={styles.userNameCol}>
                    <div className={styles.avatarMini}>
                      <span>{u.name ? u.name[0].toUpperCase() : '?'}</span>
                    </div>
                    <span className={styles.leaderName}>{u.name || 'Anonymous User'}</span>
                  </td>
                  <td className="utility-code">{u.email}</td>
                  <td>
                    <span className={`${styles.roleBadge} ${u.role === 'admin' ? styles.roleAdmin : styles.roleCitizen}`}>
                      {u.role ? u.role.toUpperCase() : 'CITIZEN'}
                    </span>
                  </td>
                  <td className="utility-code font-bold">{(u.points || 0).toLocaleString()} PTS</td>
                  <td>
                    <button 
                      className="blueprint-btn blueprint-btn-secondary" 
                      onClick={() => handleToggleRole(u.id, u.role)}
                    >
                      <Shield size={12} />
                      <span>TOGGLE ROLE</span>
                    </button>
                  </td>
                </tr>
              ))}

              {users.length === 0 && !loading && (
                <tr>
                  <td colSpan="5" className="text-center py-8">
                    <span className="utility-code">No users registered yet</span>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
