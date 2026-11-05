import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Users,
  Camera,
  CalendarCheck,
  FileSpreadsheet,
  Settings,
} from 'lucide-react';

interface SidebarProps {
  activeSessionId?: number | null;
}

export const Sidebar: React.FC<SidebarProps> = ({ activeSessionId }) => {
  const navItems = [
    {
      to: '/',
      label: 'داشبورد',
      icon: LayoutDashboard,
    },
    {
      to: '/recognition',
      label: 'کلاس زنده و تشخیص',
      icon: Camera,
      badge: activeSessionId ? 'زنده' : undefined,
    },
    {
      to: '/students',
      label: 'دانشجویان',
      icon: Users,
    },
    {
      to: '/sessions',
      label: 'جلسات کلاسی',
      icon: CalendarCheck,
    },
    {
      to: '/reports',
      label: 'گزارش‌های اکسل',
      icon: FileSpreadsheet,
    },
    {
      to: '/settings',
      label: 'وضعیت سامانه',
      icon: Settings,
    },
  ];

  return (
    <aside className="w-64 bg-surface border-l border-bone h-screen sticky top-0 flex flex-col justify-between p-4 shrink-0 select-none">
      <div>
        {/* Brand Header */}
        <div className="flex items-center gap-3 px-3 py-4 mb-6 border-b border-bone/60">
          <div className="w-9 h-9 rounded-xl bg-brand/10 border border-brand/20 flex items-center justify-center text-brand font-bold text-lg shadow-soft">
            ح
          </div>
          <div>
            <h1 className="text-sm font-bold text-ink tracking-tight">حضور و غیاب هوشمند</h1>
            <p className="text-[11px] text-ink-muted">نسخه آفلاین کلاسی</p>
          </div>
        </div>

        {/* Navigation Links */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center justify-between px-3.5 py-2.5 rounded-xl text-sm font-medium transition-all duration-150 ${
                    isActive
                      ? 'bg-brand text-white shadow-soft font-semibold'
                      : 'text-ink-muted hover:text-ink hover:bg-warmMuted/80'
                  }`
                }
              >
                {({ isActive }) => (
                  <>
                    <div className="flex items-center gap-3">
                      <Icon
                        className={`w-4 h-4 ${
                          isActive ? 'text-white' : 'text-ink-muted'
                        }`}
                      />
                      <span>{item.label}</span>
                    </div>
                    {item.badge && (
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase tracking-wider ${
                          isActive
                            ? 'bg-white/20 text-white'
                            : 'bg-accent-emeraldLight text-accent-emerald border border-accent-emeraldBorder animate-pulse'
                        }`}
                      >
                        {item.badge}
                      </span>
                    )}
                  </>
                )}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Info */}
      <div className="p-3 bg-warmMuted/60 rounded-xl border border-bone/80 text-[11px] text-ink-muted">
        <div className="flex items-center justify-between">
          <span>موتور بینایی:</span>
          <span className="font-mono text-ink">HOG (CPU)</span>
        </div>
        <div className="flex items-center justify-between mt-1">
          <span>پایگاه‌داده:</span>
          <span className="font-mono text-ink">SQLite ۳</span>
        </div>
      </div>
    </aside>
  );
};

