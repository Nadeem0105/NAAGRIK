// f:\CN Hackathon\frontend\src\app\admin\layout.js
'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { ClipboardList, Users, Building, BarChart2, ShieldAlert, Map } from 'lucide-react';
import styles from './layout.module.css';

export default function AdminLayout({ children }) {
  const { user, loading } = useApp();
  const pathname = usePathname();
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    if (!loading) {
      if (!user) {
        router.push('/login');
      } else if (user.role !== 'admin' && !user.is_admin) {
        // Not an admin, redirect to portal
        router.push('/portal');
      } else {
        setAuthorized(true);
      }
    }
  }, [user, loading, router]);

  if (loading || !authorized) {
    return (
      <div className={styles.loadingWrapper}>
        <div className="utility-code">VERIFYING AUTHORITY PROFILE...</div>
      </div>
    );
  }

  const isActive = (path) => pathname === path;

  return (
    <div className={styles.layoutContainer}>
      {/* Sidebar Navigation */}
      <aside className={styles.sidebar}>
        <div className={styles.sidebarHeader}>
          <ShieldAlert size={20} className={styles.headerIcon} />
          <div>
            <h2 className="label-caps" style={{ margin: 0, fontSize: '14px', fontWeight: 800, letterSpacing: '0.05em' }}>MUNICIPAL CONSOLE</h2>
            <span className={`${styles.sidebarScope} ${
              !user?.admin_scope || user.admin_scope === 'super' ? styles.scopeSuper :
              user.admin_scope === 'state' ? styles.scopeState : styles.scopeDistrict
            }`}>
              {!user?.admin_scope || user.admin_scope === 'super' ? 'Super Admin' :
               user.admin_scope === 'state' ? 'State Admin' : 'District Admin'}
            </span>
          </div>
        </div>
        <nav className={styles.sidebarNav}>
          <Link
            href="/admin"
            className={`${styles.sidebarLink} ${isActive('/admin') ? styles.active : ''}`}
          >
            <ClipboardList size={16} />
            <span>MANAGE ISSUES</span>
          </Link>
          {/* USER DIRECTORY — super-admin only */}
          {(user?.admin_scope === 'super' || !user?.admin_scope) && (
            <Link
              href="/admin/users"
              className={`${styles.sidebarLink} ${isActive('/admin/users') ? styles.active : ''}`}
            >
              <Users size={16} />
              <span>USER DIRECTORY</span>
            </Link>
          )}
          <Link
            href="/admin/departments"
            className={`${styles.sidebarLink} ${isActive('/admin/departments') ? styles.active : ''}`}
          >
            <Building size={16} />
            <span>DEPARTMENTS</span>
          </Link>
          {/* Municipal Analytics — all admins */}
          <Link
            href="/admin/analytics"
            className={`${styles.sidebarLink} ${isActive('/admin/analytics') ? styles.active : ''}`}
          >
            <BarChart2 size={16} />
            <span>MUNICIPAL ANALYTICS</span>
          </Link>
          {/* Regions — super-admin & state-admin */}
          {(user?.admin_scope === 'super' || user?.admin_scope === 'state' || !user?.admin_scope) && (
            <Link
              href="/admin/regions"
              className={`${styles.sidebarLink} ${isActive('/admin/regions') ? styles.active : ''}`}
            >
              <Map size={16} />
              <span>REGION MANAGEMENT</span>
            </Link>
          )}
        </nav>
      </aside>

      {/* Main Content Area */}
      <main className={styles.content}>
        {children}
      </main>
    </div>
  );
}
