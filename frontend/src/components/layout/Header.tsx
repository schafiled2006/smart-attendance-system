import React from 'react';
import { Link } from 'react-router-dom';
import { Radio, AlertCircle } from 'lucide-react';
import { Session } from '../../api/types';

interface HeaderProps {
  activeSession: Session | null;
  serverOnline: boolean;
}

export const Header: React.FC<HeaderProps> = ({ activeSession, serverOnline }) => {
  return (
    <header className="h-16 bg-surface/80 backdrop-blur-md border-b border-bone px-8 flex items-center justify-between sticky top-0 z-30">
      <div className="flex items-center gap-4">
        {activeSession ? (
          <Link
            to="/recognition"
            className="flex items-center gap-2.5 px-3 py-1.5 rounded-full bg-accent-emeraldLight/80 border border-accent-emeraldBorder text-xs text-accent-emerald hover:bg-accent-emeraldLight transition-all group"
          >
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent-emerald opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-accent-emerald"></span>
            </span>
            <span className="font-semibold">جلسه فعال #{activeSession.id}</span>
            <span className="text-ink-muted group-hover:text-ink">
              (حد تأخیر: {activeSession.late_after_minutes} دقیقه)
            </span>
          </Link>
        ) : (
          <div className="flex items-center gap-2 text-xs text-ink-muted">
            <Radio className="w-3.5 h-3.5 text-bone" />
            <span>جلسه فعالی در جریان نیست</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4 text-xs">
        {/* Server Connection Status */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-warmMuted/80 border border-bone text-ink-muted">
          <span
            className={`w-2 h-2 rounded-full ${
              serverOnline ? 'bg-accent-emerald' : 'bg-accent-crimson animate-pulse'
            }`}
          />
          <span>{serverOnline ? 'سرور متصل است' : 'قطع ارتباط با سرور'}</span>
          {!serverOnline && <AlertCircle className="w-3 h-3 text-accent-crimson" />}
        </div>
      </div>
    </header>
  );
};

