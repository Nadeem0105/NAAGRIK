// f:\CN Hackathon\frontend\src\app\login\page.js
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { Mail, Lock, LogIn, Shield, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { GoogleSignInButton } from '@/components/GoogleSignInButton';
import styles from './page.module.css';

export default function LoginPage() {
  const { user, login } = useApp();
  const router = useRouter();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);


  // Redirect if already logged in
  useEffect(() => {
    if (user) {
      if (user.role === 'admin' || user.is_admin) {
        router.push('/admin');
      } else {
        router.push('/portal');
      }
    }
  }, [user, router]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSubmitting(true);
    try {
      await login(email, password);
    } catch (err) {
      setError(err.message || 'Login failed. Verify credentials.');
      setSubmitting(false);
    }
  };

  return (
    <div className={`${styles.pageWrapper} blueprint-bg`}>
      <main className={`${styles.clipboardCard} animate-scale-up`}>
        {/* Metal Clip Aesthetic Header */}
        <div className={styles.clipHeader}>
          <div className={styles.clipHoleLeft}></div>
          <div className={styles.clipHoleRight}></div>
        </div>

        <div className={styles.cardContent}>
          {/* Logo Group */}
          <div className={`${styles.logoGroup} animate-fade-in-up delay-100`}>
            <Shield size={36} className={styles.logoIcon} />
            <h1 className={styles.title}>Community Hero</h1>
            <span className={styles.subtitle}>Sign in to your citizen dashboard</span>
          </div>

          {error && (
            <div className={`${styles.errorAlert} animate-scale-up`}>
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Form */}
          <form className={styles.form} onSubmit={handleSubmit}>
            <div className={`${styles.inputGroup} animate-fade-in-up delay-200`}>
              <label className="label-caps" htmlFor="email">Email Address</label>
              <div className={styles.inputWrapper}>
                <Mail size={16} className={styles.inputIcon} />
                <input
                  type="email"
                  id="email"
                  className={styles.input}
                  placeholder="user@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className={`${styles.inputGroup} animate-fade-in-up delay-300`}>
              <label className="label-caps" htmlFor="password">Password</label>
              <div className={styles.inputWrapper}>
                <Lock size={16} className={styles.inputIcon} />
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  className={`${styles.input} ${styles.passwordInput}`}
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className={styles.eyeBtn}
                  onClick={() => setShowPassword(!showPassword)}
                  tabIndex="-1"
                  title={showPassword ? 'Hide password' : 'Show password'}
                >
                  {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>


            <div className={`${styles.formMeta} animate-fade-in-up delay-400`}>
              <label className={styles.checkboxLabel}>
                <input type="checkbox" className={styles.checkbox} />
                <span>Remember me</span>
              </label>
              <a href="#" className={styles.resetLink}>Forgot password?</a>
            </div>

            <button
              type="submit"
              className={`${styles.submitBtn} blueprint-btn animate-fade-in-up delay-500`}
              disabled={submitting}
            >
              <span>{submitting ? 'Signing in...' : 'Sign In'}</span>
              <LogIn size={16} />
            </button>
          </form>

          <div className="animate-fade-in-up delay-500" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '1rem 0', fontSize: '0.75rem', color: '#74777B' }}>
            <div style={{ height: '1px', flex: 1, backgroundColor: 'rgba(22, 35, 43, 0.1)' }} /> 
            OR 
            <div style={{ height: '1px', flex: 1, backgroundColor: 'rgba(22, 35, 43, 0.1)' }} />
          </div>
          <div className="animate-fade-in-up delay-500">
            <GoogleSignInButton />
          </div>

          {/* Footer Link */}
          <div className={`${styles.cardFooter} animate-fade-in-up delay-600`}>
            <p className={styles.footerText}>
              New to Nagarik?<br />
              <Link href="/register" className={styles.registerLink}>
                Register here
              </Link>
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
