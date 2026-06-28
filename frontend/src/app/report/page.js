// f:\CN Hackathon\frontend\src\app\report\page.js
'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useApp } from '@/context/AppContext';
import { api } from '@/services/api';
import { 
  Camera, MapPin, AlignLeft, ArrowLeft, ArrowRight, 
  UploadCloud, CheckCircle, Check, X, ShieldAlert 
} from 'lucide-react';
import styles from './page.module.css';

export default function ReportIssuePage() {
  const { user } = useApp();
  const router = useRouter();

  // Redirect if not logged in, or if admin (admins should not file citizen reports)
  useEffect(() => {
    if (!user) {
      router.push('/login');
    } else if (user.role === 'admin') {
      router.push('/admin');
    }
  }, [user, router]);

  // Form Steps
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  // Form Fields
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(null);
  
  const [latitude, setLatitude] = useState(12.9716);
  const [longitude, setLongitude] = useState(77.5946);
  const [address, setAddress] = useState('');
  
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [categoryHint, setCategoryHint] = useState('Infrastructure');

  // Trigger geolocation on mount
  useEffect(() => {
    if (typeof window !== 'undefined' && navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setLatitude(position.coords.latitude);
          setLongitude(position.coords.longitude);
        },
        (err) => console.log('Location access denied, using defaults.')
      );
    }
  }, []);

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Image file must be under 5MB.');
        return;
      }
      setImageFile(file);
      setImagePreview(URL.createObjectURL(file));
      setError('');
    }
  };

  const handleRemoveImage = () => {
    setImageFile(null);
    setImagePreview(null);
  };

  const handleNextStep = () => {
    if (step === 1 && !imageFile) {
      // Allow proceeding without image, but warn or just proceed
      setStep(2);
    } else {
      setStep(prev => Math.min(prev + 1, 3));
    }
  };

  const handlePrevStep = () => {
    setStep(prev => Math.max(prev - 1, 1));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!title || !description) {
      setError('Title and Description are required.');
      return;
    }

    setSubmitting(true);
    setError('');

    try {
      const formData = new FormData();
      formData.append('title', title);
      formData.append('description', description);
      formData.append('latitude', latitude.toString());
      formData.append('longitude', longitude.toString());
      formData.append('category_hint', categoryHint);
      
      if (imageFile) {
        formData.append('images', imageFile);
      }

      await api.createIssue(formData);
      router.push('/portal');
    } catch (err) {
      setError(err.message || 'Failed to submit report. Please try again.');
      setSubmitting(false);
    }
  };

  return (
    <div className={`${styles.pageWrapper} blueprint-bg`}>
      <div className={styles.container}>
        
        {/* Contextual header */}
        <header className={styles.formHeader}>
          <button className={styles.cancelBtn} onClick={() => router.push('/portal')}>
            <X size={16} />
            <span className="label-caps">CANCEL REPORT</span>
          </button>
          <h1 className={styles.pageTitle}>NEW ISSUE REPORT</h1>
          <span className="utility-code text-outline">Step {step} of 3</span>
        </header>

        {/* The Card Form container */}
        <main className={styles.blueprintCard}>
          {/* Stepper progress */}
          <div className={styles.stepper}>
            <div className={`${styles.stepIndicator} ${step >= 1 ? styles.stepActive : ''}`}>
              <Camera size={14} />
              <span className="label-caps">01. EVIDENCE</span>
            </div>
            <div className={`${styles.stepIndicator} ${step >= 2 ? styles.stepActive : ''}`}>
              <MapPin size={14} />
              <span className="label-caps">02. LOCATION</span>
            </div>
            <div className={`${styles.stepIndicator} ${step >= 3 ? styles.stepActive : ''}`}>
              <AlignLeft size={14} />
              <span className="label-caps">03. DETAILS</span>
            </div>
          </div>

          {error && (
            <div className={styles.errorAlert}>
              <ShieldAlert size={16} />
              <span>{error}</span>
            </div>
          )}

          {/* Form Wizard Pages */}
          <form className={styles.form} onSubmit={handleSubmit}>
            
            {/* STEP 1: MEDIA UPLOAD */}
            {step === 1 && (
              <div className={styles.stepContent}>
                <div className={styles.sectionTitleRow}>
                  <h3 className="label-caps">Upload Photo Evidence</h3>
                  <div className={styles.line}></div>
                </div>

                {!imagePreview ? (
                  <div className={styles.dropzone}>
                    <UploadCloud size={48} className={styles.uploadIcon} />
                    <div className={styles.dropzoneText}>
                      <h4>Select or Drop Photo</h4>
                      <p className="utility-code">PNG, JPG or WEBP format (Max 5MB)</p>
                    </div>
                    <input 
                      type="file" 
                      accept="image/*" 
                      onChange={handleFileChange} 
                      className={styles.fileInput}
                    />
                  </div>
                ) : (
                  <div className={styles.previewContainer}>
                    <img src={imagePreview} alt="Evidence preview" className={styles.previewImage} />
                    <button type="button" className={styles.removeImageBtn} onClick={handleRemoveImage}>
                      <X size={16} />
                      <span>Remove File</span>
                    </button>
                  </div>
                )}
                
                <p className={styles.stepTip}>
                  Providing clear visual evidence helps the municipal team verify and resolve the issue faster.
                </p>
              </div>
            )}

            {/* STEP 2: GEOLOCATION MAP */}
            {step === 2 && (
              <div className={styles.stepContent}>
                <div className={styles.sectionTitleRow}>
                  <h3 className="label-caps">Select Location</h3>
                  <div className={styles.line}></div>
                </div>

                {/* Map Grid outline */}
                <div className={styles.locationTeaser}>
                  <div className={styles.coordinatesPanel}>
                    <div className={styles.coordGroup}>
                      <label className="label-caps">LATITUDE</label>
                      <input 
                        type="number" 
                        step="0.000001" 
                        value={latitude} 
                        onChange={e => setLatitude(parseFloat(e.target.value))}
                        className={styles.coordInput}
                      />
                    </div>
                    <div className={styles.coordGroup}>
                      <label className="label-caps">LONGITUDE</label>
                      <input 
                        type="number" 
                        step="0.000001" 
                        value={longitude} 
                        onChange={e => setLongitude(parseFloat(e.target.value))}
                        className={styles.coordInput}
                      />
                    </div>
                  </div>
                  
                  {/* Address input */}
                  <div className={styles.addressInputGroup}>
                    <label className="label-caps" htmlFor="address">Estimated Address / Landmark</label>
                    <input 
                      type="text" 
                      id="address" 
                      placeholder="e.g. 5th Ave and 42nd St intersection"
                      value={address} 
                      onChange={e => setAddress(e.target.value)}
                      className={styles.addressInput}
                    />
                  </div>
                </div>
              </div>
            )}

            {/* STEP 3: DETAILS */}
            {step === 3 && (
              <div className={styles.stepContent}>
                <div className={styles.sectionTitleRow}>
                  <h3 className="label-caps">Category & Details</h3>
                  <div className={styles.line}></div>
                </div>

                <div className={styles.detailsFormGroup}>
                  {/* Category select */}
                  <div className={styles.inputFieldGroup}>
                    <label className="label-caps" htmlFor="categoryHint">Issue Category</label>
                    <select 
                      id="categoryHint" 
                      value={categoryHint} 
                      onChange={e => setCategoryHint(e.target.value)}
                      className={styles.selectInput}
                    >
                      <option value="Infrastructure">Infrastructure (Potholes, Sidewalks)</option>
                      <option value="Sanitation">Sanitation (Trash, Graffiti, Waste)</option>
                      <option value="Public Safety">Public Safety (Streetlights, Signage)</option>
                    </select>
                  </div>

                  {/* Title */}
                  <div className={styles.inputFieldGroup}>
                    <label className="label-caps" htmlFor="title">Report Title</label>
                    <input 
                      type="text" 
                      id="title" 
                      placeholder="e.g. Displaced sewer cover" 
                      value={title} 
                      onChange={e => setTitle(e.target.value)}
                      required
                      className={styles.textInput}
                    />
                  </div>

                  {/* Description */}
                  <div className={styles.inputFieldGroup}>
                    <label className="label-caps" htmlFor="description">Detailed Description</label>
                    <textarea 
                      id="description" 
                      placeholder="Please describe the size, obstruction level, and exact position of the issue..." 
                      value={description} 
                      onChange={e => setDescription(e.target.value)}
                      required
                      rows={5}
                      className={styles.textareaInput}
                    ></textarea>
                  </div>
                </div>
              </div>
            )}

            {/* Wizard Navigation Footer */}
            <div className={styles.wizardFooter}>
              {step > 1 ? (
                <button type="button" className="blueprint-btn blueprint-btn-secondary" onClick={handlePrevStep}>
                  <ArrowLeft size={16} />
                  <span>PREVIOUS STEP</span>
                </button>
              ) : (
                <button type="button" className="blueprint-btn blueprint-btn-secondary" onClick={() => router.push('/portal')}>
                  <span>Cancel</span>
                </button>
              )}

              {step < 3 ? (
                <button type="button" className="blueprint-btn blueprint-btn-primary" onClick={handleNextStep}>
                  <span>Next Step</span>
                  <ArrowRight size={16} />
                </button>
              ) : (
                <button 
                  type="submit" 
                  disabled={submitting} 
                  className="blueprint-btn blueprint-btn-primary"
                >
                  <span>{submitting ? 'Submitting...' : 'Submit Report'}</span>
                  <Check size={16} />
                </button>
              )}
            </div>

          </form>
        </main>

      </div>
    </div>
  );
}
