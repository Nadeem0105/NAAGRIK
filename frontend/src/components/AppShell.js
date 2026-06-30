'use client';

import * as React from 'react';
import { usePathname } from 'next/navigation';
import { Preloader } from '@/components/Preloader';

export function AppShell({ children }) {
  const pathname = usePathname();
  // Only show the preloader if the very first page the user lands on is the home page
  const [loading, setLoading] = React.useState(pathname === '/');

  return (
    <>
      {loading && <Preloader onComplete={() => setLoading(false)} />}
      <div>{children}</div>
    </>
  );
}
