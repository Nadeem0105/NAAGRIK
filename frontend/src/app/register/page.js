// f:\CN Hackathon\frontend\src\app\register\page.js
'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { UserPlus, User, Mail, Lock, Shield, AlertTriangle, Eye, EyeOff } from 'lucide-react';
import { GoogleSignInButton } from '@/components/GoogleSignInButton';
import styles from './page.module.css';

export default function RegisterPage() {
  const { user, register } = useApp();
  const router = useRouter();

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
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
    
    if (password !== confirmPassword) {
      setError('Passwords do not match.');
      return;
    }

    setSubmitting(true);
    try {
      await register(name, email, password);
    } catch (err) {
      setError(err.message || 'Registration failed. Try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className={`${styles.pageWrapper} blueprint-bg`}>
      <div className={styles.container}>
        {/* Header / Logo */}
        <div className={`${styles.logoHeader} animate-fade-in-up`}>
          <h1 className={styles.appTitle}>COMMUNITY HERO</h1>
          <p className={styles.appSubtitle}>Citizen Registration Portal</p>
        </div>

        {/* Card */}
        <main className={`${styles.blueprintCard} animate-scale-up delay-100`}>
          <div className={styles.cardHeader}>
            <UserPlus size={16} className={styles.headerIcon} />
            <span className="label-caps">Create Account</span>
          </div>

          {error && (
            <div className={`${styles.errorAlert} animate-scale-up`}>
              <AlertTriangle size={16} />
              <span>{error}</span>
            </div>
          )}

          <form className={styles.form} onSubmit={handleSubmit}>
            {/* Full Name */}
            <div className={`${styles.inputGroup} animate-fade-in-up delay-200`}>
              <label className="label-caps" htmlFor="name">Full Name</label>
              <div className={styles.inputWrapper}>
                <User size={16} className={styles.inputIcon} />
                <input
                  type="text"
                  id="name"
                  className={styles.input}
                  placeholder="John Doe"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Email */}
            <div className={`${styles.inputGroup} animate-fade-in-up delay-300`}>
              <label className="label-caps" htmlFor="email">Email Address</label>
              <div className={styles.inputWrapper}>
                <Mail size={16} className={styles.inputIcon} />
                <input
                  type="email"
                  id="email"
                  className={styles.input}
                  placeholder="john.doe@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            {/* Password */}
            <div className={`${styles.inputGroup} animate-fade-in-up delay-400`}>
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

            {/* Confirm Password */}
            <div className={`${styles.inputGroup} animate-fade-in-up delay-500`}>
              <label className="label-caps" htmlFor="confirmPassword">Confirm Password</label>
              <div className={styles.inputWrapper}>
                <Lock size={16} className={styles.inputIcon} />
                <input
                  type={showConfirmPassword ? 'text' : 'password'}
                  id="confirmPassword"
                  className={`${styles.input} ${styles.passwordInput}`}
                  placeholder="••••••••"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
                <button
                  type="button"
                  className={styles.eyeBtn}
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  tabIndex="-1"
                  title={showConfirmPassword ? 'Hide password' : 'Show password'}
                >
                  {showConfirmPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>


            {/* Terms checkbox */}
            <div className={`${styles.checkboxWrapper} animate-fade-in-up delay-600`}>
              <input type="checkbox" id="terms" className={styles.checkbox} required />
              <label htmlFor="terms" className={styles.checkboxLabel}>
                I acknowledge the <a href="#" className={styles.termsLink}>Civic Duty Guidelines</a> and <a href="#" className={styles.termsLink}>Data Policy</a>.
              </label>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              className={`${styles.submitBtn} blueprint-btn animate-fade-in-up delay-700`}
              disabled={submitting}
            >
              <span>{submitting ? 'Registering...' : 'Create Account'}</span>
            </button>
          </form>

          <div className="animate-fade-in-up delay-700" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', margin: '1rem 0', fontSize: '0.75rem', color: '#74777B' }}>
            <div style={{ height: '1px', flex: 1, backgroundColor: 'rgba(22, 35, 43, 0.1)' }} /> 
            OR 
            <div style={{ height: '1px', flex: 1, backgroundColor: 'rgba(22, 35, 43, 0.1)' }} />
          </div>
          <div className="animate-fade-in-up delay-700">
            <GoogleSignInButton />
          </div>

          {/* Footer Navigation */}
          <div className={`${styles.cardFooter} animate-fade-in-up delay-800`}>
            <p className={styles.footerText}>
              Already registered?
              <Link href="/login" className={styles.loginLink}>
                Login to Portal
              </Link>
            </p>
          </div>
        </main>

      </div>
    </div>
  );
}
