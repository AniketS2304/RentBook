import React from 'react';

// ==========================================
// Card
// ==========================================
export interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
  className?: string;
}

export const Card: React.FC<CardProps> = ({ children, style, ...props }) => (
  <div
    style={{
      backgroundColor: '#ffffff',
      border: '1px solid #e2e8f0',
      borderRadius: 12,
      padding: 16,
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.04)',
      ...style,
    }}
    {...props}
  >
    {children}
  </div>
);

// ==========================================
// Badge (Semantic Status Presentation)
// ==========================================
export type BadgeVariant = 'PAID' | 'DUE' | 'OVERDUE' | 'PARTIALLY_PAID' | 'PENDING' | 'DEFAULT';

interface BadgeProps {
  status: string;
  label?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, label }) => {
  const normalized = status.toUpperCase();

  let bg = '#f1f5f9';
  let color = '#475569';
  let border = '#cbd5e1';

  if (normalized === 'PAID') {
    bg = '#dcfce7';
    color = '#15803d';
    border = '#bbf7d0';
  } else if (normalized === 'DUE') {
    bg = '#fef3c7';
    color = '#b45309';
    border = '#fde68a';
  } else if (normalized === 'OVERDUE') {
    bg = '#fee2e2';
    color = '#b91c1c';
    border = '#fecaca';
  } else if (normalized === 'PARTIALLY_PAID' || normalized === 'PARTIAL') {
    bg = '#e0f2fe';
    color = '#0369a1';
    border = '#bae6fd';
  } else if (normalized === 'PENDING') {
    bg = '#f8fafc';
    color = '#64748b';
    border = '#e2e8f0';
  }

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding: '3px 8px',
        borderRadius: 9999,
        fontSize: 11,
        fontWeight: 600,
        textTransform: 'uppercase',
        letterSpacing: '0.04em',
        backgroundColor: bg,
        color,
        border: `1px solid ${border}`,
      }}
    >
      {label || normalized.replace('_', ' ')}
    </span>
  );
};

// ==========================================
// Button
// ==========================================
export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled,
  style,
  ...props
}) => {
  let bg = '#2563eb';
  let color = '#ffffff';
  let border = 'none';

  if (variant === 'secondary') {
    bg = '#f1f5f9';
    color = '#1e293b';
  } else if (variant === 'outline') {
    bg = 'transparent';
    color = '#2563eb';
    border = '1px solid #2563eb';
  } else if (variant === 'danger') {
    bg = '#dc2626';
    color = '#ffffff';
  }

  const padding = size === 'sm' ? '6px 12px' : size === 'lg' ? '14px 24px' : '10px 18px';
  const fontSize = size === 'sm' ? 13 : 14;

  return (
    <button
      disabled={disabled}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding,
        fontSize,
        fontWeight: 600,
        borderRadius: 8,
        backgroundColor: bg,
        color,
        border,
        minHeight: size === 'sm' ? 36 : 44,
        cursor: disabled ? 'not-allowed' : 'pointer',
        opacity: disabled ? 0.6 : 1,
        transition: 'background-color 0.15s ease',
        ...style,
      }}
      {...props}
    >
      {children}
    </button>
  );
};

// ==========================================
// Loading Skeleton
// ==========================================
export const Skeleton: React.FC<{ height?: number | string; width?: number | string; borderRadius?: number }> = ({
  height = 20,
  width = '100%',
  borderRadius = 6,
}) => (
  <div
    style={{
      height,
      width,
      borderRadius,
      backgroundColor: '#f1f5f9',
      animation: 'pulse 1.5s infinite ease-in-out',
    }}
  />
);

export const DashboardSkeleton: React.FC = () => (
  <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
      <Skeleton height={28} width="50%" />
      <Skeleton height={32} width={120} />
    </div>
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
      <Skeleton height={80} />
      <Skeleton height={80} />
      <Skeleton height={80} />
    </div>
    <Skeleton height={60} />
    <Skeleton height={140} />
    <Skeleton height={140} />
  </div>
);

// ==========================================
// Empty State
// ==========================================
export interface EmptyStateProps {
  title?: string;
  description: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: string;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title = 'Welcome to RentBook 👋',
  description,
  actionLabel,
  onAction,
  icon = '🏢',
}) => (
  <Card style={{ textAlign: 'center', padding: '36px 20px', margin: '20px 0' }}>
    <div style={{ fontSize: 40, marginBottom: 12 }}>{icon}</div>
    <h3 style={{ fontSize: 18, fontWeight: 700, color: '#0f172a', marginBottom: 8 }}>{title}</h3>
    <p style={{ fontSize: 14, color: '#64748b', maxWidth: 300, margin: '0 auto 20px', lineHeight: 1.5 }}>
      {description}
    </p>
    {actionLabel && onAction && (
      <Button variant="primary" onClick={onAction}>
        {actionLabel}
      </Button>
    )}
  </Card>
);

// ==========================================
// Error State
// ==========================================
export interface ErrorStateProps {
  message?: string;
  onRetry: () => void;
}

export const ErrorState: React.FC<ErrorStateProps> = ({
  message = "Couldn't load your dashboard.",
  onRetry,
}) => (
  <Card style={{ textAlign: 'center', padding: '28px 16px', margin: '20px 0', borderColor: '#fecaca', backgroundColor: '#fef2f2' }}>
    <div style={{ fontSize: 32, marginBottom: 8 }}>⚠️</div>
    <h3 style={{ fontSize: 16, fontWeight: 600, color: '#991b1b', marginBottom: 14 }}>
      {message}
    </h3>
    <Button variant="outline" size="sm" onClick={onRetry} style={{ borderColor: '#dc2626', color: '#dc2626' }}>
      Retry
    </Button>
  </Card>
);
