// f:\CN Hackathon\frontend\src\context\AppContext.js
'use client';

import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '@/services/api';
import { useRouter, usePathname } from 'next/navigation';

const AppContext = createContext();

export function AppProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [notifications, setNotifications] = useState([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [locationUpdated, setLocationUpdated] = useState(false);
  const router = useRouter();
  const pathname = usePathname();

  const fetchUser = useCallback(async () => {
    try {
      const u = await api.getMe();
      setUser(u);
      return u;
    } catch (err) {
      // Token is invalid or expired
      setUser(null);
      if (typeof window !== 'undefined') {
        localStorage.removeItem('token');
      }
    }
  }, []);

  const fetchNotifications = useCallback(async () => {
    if (!localStorage.getItem('token')) return;
    try {
      const list = await api.listNotifications(1, 20);
      setNotifications(list);
      setUnreadCount(list.filter(n => !n.is_read).length);
    } catch (err) {
      console.error('Failed to fetch notifications:', err);
    }
  }, []);

  useEffect(() => {
    const init = async () => {
      if (typeof window !== 'undefined' && window.location.pathname.startsWith('/auth/callback')) {
        // Let the callback page handle initialization with the new token
        return;
      }
      const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;
      if (token) {
        await fetchUser();
        await fetchNotifications();
      } else {
        setUser(null);
      }
      setLoading(false);
    };
    init();
  }, [fetchUser, fetchNotifications]);

  // Automatically update location region if geolocation is available and user is logged in
  useEffect(() => {
    if (user && !locationUpdated && user.role !== 'admin') {
      if (typeof window !== 'undefined' && navigator.geolocation) {
        navigator.geolocation.getCurrentPosition(
          async (position) => {
            const { latitude, longitude } = position.coords;
            try {
              const updatedUser = await api.updateLocation(latitude, longitude);
              setUser(updatedUser);
              setLocationUpdated(true);
            } catch (err) {
              console.error('Failed to auto-update location region:', err);
            }
          },
          (error) => {
            console.warn('Geolocation permission denied or failed:', error);
          }
        );
      }
    }
  }, [user, locationUpdated]);

  // Handle redirect if not logged in
  // Public paths: landing, auth pages, and read-only data pages (leaderboard, explore, issue details)
  useEffect(() => {
    const publicPaths = ['/', '/login', '/register', '/leaderboard', '/explore', '/auth/callback'];
    const isPublicPath = publicPaths.includes(pathname) || pathname.startsWith('/issues/');
    if (!loading && !user && !isPublicPath) {
      router.push('/login');
    }
  }, [user, loading, pathname, router]);

  const login = async (email, password) => {
    setLoading(true);
    try {
      await api.login(email, password);
      setLocationUpdated(false);
      const u = await fetchUser();
      await fetchNotifications();
      if (u.role === 'admin' || u.is_admin) {
        router.push('/admin');
      } else {
        router.push('/portal');
      }
    } finally {
      setLoading(false);
    }
  };

  const register = async (name, email, password) => {
    setLoading(true);
    try {
      await api.register(name, email, password);
      setLocationUpdated(false);
      await fetchUser();
      await fetchNotifications();
      router.push('/portal');
    } finally {
      setLoading(false);
    }
  };

  const handleTokenLogin = useCallback(async (token) => {
    setLoading(true);
    try {
      if (typeof window !== 'undefined') {
        localStorage.setItem('token', token);
      }
      // Re-configure api with new token if api object caches it, though usually it reads from localStorage
      setLocationUpdated(false);
      const u = await fetchUser();
      if (u) {
        await fetchNotifications();
        if (u.role === 'admin' || u.is_admin) {
          router.push('/admin');
        } else {
          router.push('/portal');
        }
      } else {
        router.push('/login?error=auth_failed');
      }
    } finally {
      setLoading(false);
    }
  }, [fetchUser, fetchNotifications, router]);

  const logout = () => {
    api.logout();
    setUser(null);
    setNotifications([]);
    setUnreadCount(0);
    setLocationUpdated(false);
    router.push('/login');
  };

  const markRead = async (id) => {
    try {
      await api.markNotificationAsRead(id);
      await fetchNotifications();
    } catch (err) {
      console.error('Failed to mark read:', err);
    }
  };

  return (
    <AppContext.Provider value={{
      user,
      loading,
      notifications,
      unreadCount,
      login,
      register,
      handleTokenLogin,
      logout,
      markRead,
      fetchUser,
      fetchNotifications,
    }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within an AppProvider');
  }
  return context;
}
