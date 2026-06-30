'use client';

import React, { useEffect, useRef } from 'react';

export function GooeyText({
  texts,
  morphTime = 1,
  cooldownTime = 0.25,
  className,
  textColor = '#16232b',
  textGlow = 'none',
  stopOnLast = true,
  onTextChange,
}) {
  const text1Ref = useRef(null);
  const text2Ref = useRef(null);
  const containerRef = useRef(null);
  
  // Keep track of the latest dynamic props without triggering a re-render
  // of the animation loop
  const styleProps = useRef({ textGlow, textColor });
  
  useEffect(() => {
    styleProps.current = { textGlow, textColor };
  }, [textGlow, textColor]);

  useEffect(() => {
    if (!texts || texts.length === 0) return;
    
    let textIndex = texts.length - 1;
    let time = performance.now();
    let morph = 0;
    let cooldown = cooldownTime;
    let animationFrameId;

    if (text1Ref.current && text2Ref.current) {
      text1Ref.current.textContent = texts[textIndex % texts.length];
      text2Ref.current.textContent = texts[(textIndex + 1) % texts.length];
    }

    function getBaseFilter() {
      const tg = styleProps.current.textGlow;
      return tg && tg !== 'none' ? `${tg} ` : '';
    }

    function setMorph(fraction) {
      if (!text2Ref.current || !text1Ref.current) return;
      const blurVal2 = Math.min(8 / fraction - 8, 100);
      const blurVal1 = Math.min(8 / (1 - fraction) - 8, 100);
      
      text2Ref.current.style.filter = `${getBaseFilter()}blur(${blurVal2}px)`;
      text2Ref.current.style.opacity = `${Math.pow(fraction, 0.4) * 100}%`;

      text1Ref.current.style.filter = `${getBaseFilter()}blur(${blurVal1}px)`;
      text1Ref.current.style.opacity = `${Math.pow(1 - fraction, 0.4) * 100}%`;
    }

    function doMorph() {
      morph -= cooldown;
      cooldown = 0;

      let fraction = morph / morphTime;

      if (fraction > 1) {
        cooldown = cooldownTime;
        fraction = 1;
      }

      setMorph(fraction);
    }

    function doCooldown() {
      morph = 0;
      if (!text2Ref.current || !text1Ref.current) return;
      text2Ref.current.style.filter = getBaseFilter().trim();
      text2Ref.current.style.opacity = '100%';
      text1Ref.current.style.filter = getBaseFilter().trim();
      text1Ref.current.style.opacity = '0%';
    }

    function animate(currentTime) {
      animationFrameId = requestAnimationFrame(animate);

      const shouldIncrementIndex = cooldown > 0;
      const dt = (currentTime - time) / 1000;
      time = currentTime;

      cooldown -= dt;

      if (cooldown <= 0) {
        if (shouldIncrementIndex) {
          if (stopOnLast && textIndex === texts.length - 2) {
            cancelAnimationFrame(animationFrameId);
            doCooldown();
            return;
          }
          textIndex = (textIndex + 1) % texts.length;
          if (text1Ref.current && text2Ref.current) {
            text1Ref.current.textContent = texts[textIndex % texts.length];
            text2Ref.current.textContent = texts[(textIndex + 1) % texts.length];
          }
          onTextChange?.(texts[(textIndex + 1) % texts.length]);
        }
        doMorph();
      } else {
        doCooldown();
      }
    }

    animationFrameId = requestAnimationFrame(animate);

    return () => {
      cancelAnimationFrame(animationFrameId);
    };
  }, [texts, morphTime, cooldownTime, onTextChange, stopOnLast]);

  return (
    <div style={{ position: 'relative', width: '100%', height: '8rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }} ref={containerRef}>
      <svg width="0" height="0" style={{ position: 'absolute', pointerEvents: 'none' }} aria-hidden="true" focusable="false">
        <defs>
          <filter id="gooey">
            <feColorMatrix
              in="SourceGraphic"
              type="matrix"
              values="1 0 0 0 0  0 1 0 0 0  0 0 1 0 0  0 0 0 255 -140"
            />
          </filter>
        </defs>
      </svg>
      <div style={{ filter: 'url(#gooey)', position: 'absolute', inset: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <span
          ref={text1Ref}
          style={{ position: 'absolute', textAlign: 'center', userSelect: 'none', letterSpacing: '-0.025em', fontSize: '4.5rem', fontWeight: 700, fontFamily: 'var(--font-archivo)', color: textColor, willChange: 'filter, opacity', transform: 'translateZ(0)' }}
        />
        <span
          ref={text2Ref}
          style={{ position: 'absolute', textAlign: 'center', userSelect: 'none', letterSpacing: '-0.025em', fontSize: '4.5rem', fontWeight: 700, fontFamily: 'var(--font-archivo)', color: textColor, willChange: 'filter, opacity', transform: 'translateZ(0)' }}
        />
      </div>
    </div>
  );
}
