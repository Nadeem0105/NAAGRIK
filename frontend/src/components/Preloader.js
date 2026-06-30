'use client';

import * as React from 'react';
import { GooeyText } from '@/components/ui/gooey-text-morphing';

const WORDS = ['Spot', 'Report', 'Verify', 'Resolve', 'Nagarik'];

export function Preloader({ onComplete }) {
  const [activeWord, setActiveWord] = React.useState(WORDS[0]);
  const [minDurationDone, setMinDurationDone] = React.useState(false);
  const [isFadingOut, setIsFadingOut] = React.useState(false);

  React.useEffect(() => {
    // guarantees the sequence is seen at least once, regardless of real load speed
    const timer = setTimeout(() => setMinDurationDone(true), 3800);
    return () => clearTimeout(timer);
  }, []);

  React.useEffect(() => {
    if (minDurationDone) {
      setIsFadingOut(true);
      // Wait for the fade out transition to finish before actually unmounting
      const timer = setTimeout(() => onComplete(), 800);
      return () => clearTimeout(timer);
    }
  }, [minDurationDone, onComplete]);

  const isNagarik = activeWord === 'Nagarik';

  return (
    <div
      role="status"
      aria-label="Loading Nagarik"
      style={{
        position: 'fixed',
        top: 0, right: 0, bottom: 0, left: 0,
        zIndex: 100,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#000000',
        opacity: isFadingOut ? 0 : 1,
        transition: 'opacity 0.8s ease-in-out',
        pointerEvents: isFadingOut ? 'none' : 'all'
      }}
    >
      <GooeyText
        texts={WORDS}
        morphTime={0.6}
        cooldownTime={0.15}
        onTextChange={setActiveWord}
        textColor={isNagarik ? '#E8A23C' : '#FFFFFF'}
        textGlow={
          isNagarik 
            ? (typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'none' : 'drop-shadow(0 0 18px rgba(232, 162, 60, 0.45))')
            : 'none'
        }
      />
    </div>
  );
}
