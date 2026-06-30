// f:\CN Hackathon\frontend\src\app\auth\callback\page.js
'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import { useApp } from '@/context/AppContext';

function AuthCallbackHandler() {
  const searchParams = useSearchParams();
  const { handleTokenLogin } = useApp();
  
  useEffect(() => {
    const token = searchParams.get('token');
    if (token) {
      handleTokenLogin(token);
    } else {
      console.error('No token found in callback URL.');
    }
  }, [searchParams, handleTokenLogin]);

  return (
    <div className="flex min-h-screen items-center justify-center blueprint-bg">
      <div className="flex flex-col items-center gap-4 text-[#16232B]">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-[#16232B] border-t-transparent"></div>
        <p className="font-body font-medium">Authenticating...</p>
      </div>
    </div>
  );
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="flex min-h-screen items-center justify-center blueprint-bg">
        <p className="font-body">Loading...</p>
      </div>
    }>
      <AuthCallbackHandler />
    </Suspense>
  );
}
