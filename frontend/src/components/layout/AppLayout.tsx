import React, { useEffect, useState } from 'react';
import { Outlet } from 'react-router-dom';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { fetchActiveSession } from '../../api/sessions';
import { checkSystemHealth } from '../../api/reports';
import { Session } from '../../api/types';

export const AppLayout: React.FC = () => {
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [serverOnline, setServerOnline] = useState<boolean>(true);

  // Poll active session & health every 5 seconds
  useEffect(() => {
    let isMounted = true;

    const checkStatus = async () => {
      try {
        const [session, health] = await Promise.all([
          fetchActiveSession().catch(() => null),
          checkSystemHealth().catch(() => null),
        ]);
        if (isMounted) {
          setActiveSession(session);
          setServerOnline(health?.status === 'ok');
        }
      } catch {
        if (isMounted) setServerOnline(false);
      }
    };

    checkStatus();
    const timer = setInterval(checkStatus, 5000);
    return () => {
      isMounted = false;
      clearInterval(timer);
    };
  }, []);

  return (
    <div className="flex min-h-screen bg-canvas font-sans selection:bg-brand/20 selection:text-brand">
      <Sidebar activeSessionId={activeSession?.id} />
      <div className="flex-1 flex flex-col min-w-0">
        <Header activeSession={activeSession} serverOnline={serverOnline} />
        <main className="flex-1 p-8 overflow-y-auto">
          <Outlet context={{ activeSession, setActiveSession }} />
        </main>
      </div>
    </div>
  );
};

