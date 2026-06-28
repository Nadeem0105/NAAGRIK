// f:\CN Hackathon\frontend\src\components\Navbar.js
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { Bell, LogOut, ShieldAlert, Award, User, Menu, X } from 'lucide-react';
import styles from './Navbar.module.css';

export default function Navbar() {
  const { user, logout, notifications, unreadCount, markRead } = useApp();
  const pathname = usePathname();
  const [showNotif, setShowNotif] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setScrolled(window.scrollY > 40);
    };
    // Initialize state
    handleScroll();
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const isActive = (path) => pathname === path;

  return (
    <header className={`${styles.header} ${scrolled ? styles.scrolled : ''}`}>
      <div className={styles.container}>
        <div className={styles.logoGroup}>
          <Link href={user ? '/portal' : '/'} className={styles.logoLink}>
            <span className={styles.logoMain}>NAGARIK</span>
            <span className={styles.logoSub}>COMMUNITY HERO</span>
          </Link>
          {/* Jurisdictional scope label for all admins */}
          {user?.role === 'admin' && (
            <span 
              className={`${styles.scopeTag} ${
                !user.admin_scope || user.admin_scope === 'super' ? styles.scopeSuper :
                user.admin_scope === 'state' ? styles.scopeState : styles.scopeDistrict
              }`} 
              title="Your administrative jurisdiction"
            >
              {!user.admin_scope || user.admin_scope === 'super' ? 'SUPER ADMIN' :
               user.admin_scope === 'state' ? 'STATE ADMIN' : 'DISTRICT ADMIN'}
            </span>
          )}
        </div>

        {/* Mobile menu toggle */}
        <button className={styles.menuToggle} onClick={() => setMenuOpen(!menuOpen)}>
          {menuOpen ? <X size={20} /> : <Menu size={20} />}
        </button>

        {/* Navigation Links */}
        <nav className={`${styles.nav} ${menuOpen ? styles.navOpen : ''}`}>
          {user && (
            <>
              {/* Dashboard is restricted to Super Admins only */}
              {user.role === 'admin' && (!user.admin_scope || user.admin_scope === 'super') && (
                <Link
                  href="/dashboard"
                  className={`${styles.navLink} ${isActive('/dashboard') ? styles.active : ''}`}
                  onClick={() => setMenuOpen(false)}
                >
                  DASHBOARD
                </Link>
              )}
              <Link
                href="/portal"
                className={`${styles.navLink} ${isActive('/portal') ? styles.active : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                FEED
              </Link>
              <Link
                href="/explore"
                className={`${styles.navLink} ${isActive('/explore') ? styles.active : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                EXPLORE MAP
              </Link>
              <Link
                href="/leaderboard"
                className={`${styles.navLink} ${isActive('/leaderboard') ? styles.active : ''}`}
                onClick={() => setMenuOpen(false)}
              >
                LEADERBOARD
              </Link>

              {/* Citizen-only links */}
              {user.role !== 'admin' && (
                <>
                  <Link
                    href="/report"
                    className={`${styles.navLink} ${isActive('/report') ? styles.active : ''}`}
                    onClick={() => setMenuOpen(false)}
                  >
                    REPORT ISSUE
                  </Link>
                  <Link
                    href="/profile"
                    className={`${styles.navLink} ${isActive('/profile') ? styles.active : ''}`}
                    onClick={() => setMenuOpen(false)}
                  >
                    MY PROFILE
                  </Link>
                </>
              )}
            </>
          )}
          {!user && (
            <>
              <Link href="/" className={styles.navLink} onClick={() => setMenuOpen(false)}>
                HOME
              </Link>
              <Link href="/login" className={styles.navLink} onClick={() => setMenuOpen(false)}>
                SIGN IN
              </Link>
              <Link href="/register" className={styles.navLink} onClick={() => setMenuOpen(false)}>
                JOIN NOW
              </Link>
            </>
          )}
        </nav>

        {/* User Actions & Notifications */}
        {user && (
          <div className={styles.userActions}>
            <div className={styles.pointsBadge} title="Your accumulated points">
              <Award size={14} className={styles.pointsIcon} />
              <span className="utility-code">{user.points || 0} PTS</span>
            </div>

            {/* Admin Switcher */}
            {(user.role === 'admin' || user.is_admin) && (
              <Link href="/admin" className={styles.adminBadge} title="Go to Admin Console">
                <ShieldAlert size={14} />
                <span>ADMIN</span>
              </Link>
            )}

            {/* Super-admin / State-admin region manager shortcut */}
            {user.role === 'admin' && (user.admin_scope === 'super' || user.admin_scope === 'state' || !user.admin_scope) && (
              <Link href="/admin/regions" className={styles.adminBadge} title="Manage Regions" style={{background: 'rgba(233,168,58,0.13)', borderColor: 'rgba(233,168,58,0.4)'}}>
                <span>REGIONS</span>
              </Link>
            )}

            {/* Notifications Dropdown Container */}
            <div className={styles.notifWrapper}>
              <button
                className={`${styles.iconBtn} ${unreadCount > 0 ? styles.bellActive : ''}`}
                onClick={() => setShowNotif(!showNotif)}
                title="Notifications"
              >
                <Bell size={18} />
                {unreadCount > 0 && <span className={styles.badgeCount}>{unreadCount}</span>}
              </button>

              {showNotif && (
                <div className={styles.notifDropdown}>
                  <div className={styles.notifHeader}>
                    <span className="label-caps">In-App Alerts</span>
                    {unreadCount > 0 && (
                      <span className={styles.unreadHeader}>{unreadCount} unread</span>
                    )}
                  </div>
                  <div className={styles.notifList}>
                    {notifications.length === 0 ? (
                      <div className={styles.emptyNotif}>No notifications yet</div>
                    ) : (
                      notifications.map((notif) => (
                        <div
                          key={notif.id}
                          className={`${styles.notifItem} ${!notif.is_read ? styles.unreadItem : ''}`}
                          onClick={() => {
                            if (!notif.is_read) markRead(notif.id);
                          }}
                        >
                          <p className={styles.notifText}>{notif.message}</p>
                          <span className={styles.notifTime}>
                            {new Date(notif.created_at).toLocaleString()}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Log Out */}
            <button className={styles.iconBtn} onClick={logout} title="Log Out">
              <LogOut size={18} />
            </button>
          </div>
        )}
      </div>
    </header>
  );
}
