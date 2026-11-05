import React from 'react';

type BadgeVariant = 'present' | 'late' | 'absent' | 'active' | 'closed' | 'neutral' | 'success';

interface BadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  size?: 'sm' | 'md';
  pulse?: boolean;
}

export const Badge: React.FC<BadgeProps> = ({
  variant,
  children,
  size = 'md',
  pulse = false,
}) => {
  const variantStyles: Record<BadgeVariant, string> = {
    present: 'bg-accent-emeraldLight text-accent-emerald border-accent-emeraldBorder',
    late: 'bg-accent-amberLight text-accent-amber border-accent-amberBorder',
    absent: 'bg-accent-crimsonLight text-accent-crimson border-accent-crimsonBorder',
    active: 'bg-brand-light text-brand border-brand-border',
    closed: 'bg-warmMuted text-ink-muted border-bone',
    neutral: 'bg-warmMuted text-ink border-bone',
    success: 'bg-accent-emeraldLight text-accent-emerald border-accent-emeraldBorder',
  };

  const sizeStyles = {
    sm: 'text-xs px-2 py-0.5',
    md: 'text-xs px-2.5 py-1 font-medium',
  };

  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border tracking-wide transition-colors ${
        variantStyles[variant]
      } ${sizeStyles[size]}`}
    >
      {pulse && (
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-current opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-current"></span>
        </span>
      )}
      {children}
    </span>
  );
};

