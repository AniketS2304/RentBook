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
  size?: 'sm' | 'md';
}

export const Badge: React.FC<BadgeProps> = ({ status, label, size = 'md' }) => {
  const normalized = status.toUpperCase();

  let bg = '#f1f5f9';
  let color = '#475569';
  let border = '#cbd5e1';

  if (normalized === 'PAID' || normalized === 'OCCUPIED') {
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
  } else if (normalized === 'PENDING' || normalized === 'VACANT') {
    bg = '#f8fafc';
    color = '#64748b';
    border = '#e2e8f0';
  } else if (normalized === 'FLAT' || normalized === 'ROOM' || normalized === 'SHOP' || normalized === 'OTHER') {
    bg = '#f1f5f9';
    color = '#334155';
    border = '#cbd5e1';
  }

  const padding = size === 'sm' ? '2px 6px' : '3px 8px';
  const fontSize = size === 'sm' ? 10 : 11;

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        padding,
        borderRadius: 9999,
        fontSize,
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
  loading?: boolean;
}

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  disabled,
  loading = false,
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
      disabled={disabled || loading}
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
        cursor: disabled || loading ? 'not-allowed' : 'pointer',
        opacity: disabled || loading ? 0.6 : 1,
        transition: 'background-color 0.15s ease',
        ...style,
      }}
      {...props}
    >
      {loading ? 'Please wait...' : children}
    </button>
  );
};

// ==========================================
// Form Controls: Input & Select
// ==========================================
export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string | null;
  helperText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  id,
  style,
  ...props
}) => {
  const inputId = id || label.toLowerCase().replace(/\s+/g, '-');
  return (
    <div style={{ marginBottom: 14 }}>
      <label
        htmlFor={inputId}
        style={{
          display: 'block',
          fontSize: 13,
          fontWeight: 600,
          color: '#334155',
          marginBottom: 4,
        }}
      >
        {label}
      </label>
      <input
        id={inputId}
        style={{
          width: '100%',
          padding: '10px 12px',
          fontSize: 14,
          borderRadius: 8,
          border: error ? '1px solid #dc2626' : '1px solid #cbd5e1',
          outline: 'none',
          boxSizing: 'border-box',
          backgroundColor: '#ffffff',
          color: '#0f172a',
          ...style,
        }}
        {...props}
      />
      {error && (
        <span style={{ display: 'block', fontSize: 12, color: '#dc2626', marginTop: 4 }}>
          {error}
        </span>
      )}
      {!error && helperText && (
        <span style={{ display: 'block', fontSize: 12, color: '#64748b', marginTop: 4 }}>
          {helperText}
        </span>
      )}
    </div>
  );
};

export interface SelectProps extends React.SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  error?: string | null;
  helperText?: string;
  options: Array<{ value: string; label: string }>;
}

export const Select: React.FC<SelectProps> = ({
  label,
  error,
  helperText,
  options,
  id,
  style,
  ...props
}) => {
  const selectId = id || label.toLowerCase().replace(/\s+/g, '-');
  return (
    <div style={{ marginBottom: 14 }}>
      <label
        htmlFor={selectId}
        style={{
          display: 'block',
          fontSize: 13,
          fontWeight: 600,
          color: '#334155',
          marginBottom: 4,
        }}
      >
        {label}
      </label>
      <select
        id={selectId}
        style={{
          width: '100%',
          padding: '10px 12px',
          fontSize: 14,
          borderRadius: 8,
          border: error ? '1px solid #dc2626' : '1px solid #cbd5e1',
          outline: 'none',
          boxSizing: 'border-box',
          backgroundColor: '#ffffff',
          color: '#0f172a',
          ...style,
        }}
        {...props}
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
      {error && (
        <span style={{ display: 'block', fontSize: 12, color: '#dc2626', marginTop: 4 }}>
          {error}
        </span>
      )}
      {!error && helperText && (
        <span style={{ display: 'block', fontSize: 12, color: '#64748b', marginTop: 4 }}>
          {helperText}
        </span>
      )}
    </div>
  );
};

// ==========================================
// Modal
// ==========================================
export interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export const Modal: React.FC<ModalProps> = ({ isOpen, onClose, title, children }) => {
  if (!isOpen) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      style={{
        position: 'fixed',
        inset: 0,
        backgroundColor: 'rgba(15, 23, 42, 0.5)',
        display: 'flex',
        alignItems: 'flex-end',
        justifyContent: 'center',
        zIndex: 100,
      }}
      onClick={onClose}
    >
      <div
        style={{
          backgroundColor: '#ffffff',
          width: '100%',
          maxWidth: 500,
          borderTopLeftRadius: 16,
          borderTopRightRadius: 16,
          padding: '20px 16px 28px',
          maxHeight: '90vh',
          overflowY: 'auto',
          boxShadow: '0 -4px 20px rgba(0,0,0,0.15)',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ fontSize: 17, fontWeight: 700, color: '#0f172a', margin: 0 }}>{title}</h2>
          <button
            onClick={onClose}
            aria-label="Close dialog"
            style={{
              background: 'none',
              border: 'none',
              fontSize: 18,
              color: '#64748b',
              cursor: 'pointer',
              padding: 4,
            }}
          >
            ✕
          </button>
        </div>
        {children}
      </div>
    </div>
  );
};

// ==========================================
// Confirm Dialog
// ==========================================
export interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isDanger?: boolean;
  loading?: boolean;
}

export const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirm',
  cancelText = 'Cancel',
  isDanger = true,
  loading = false,
}) => {
  if (!isOpen) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={title}>
      <p style={{ fontSize: 14, color: '#475569', lineHeight: 1.5, margin: '0 0 20px 0' }}>
        {message}
      </p>
      <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end' }}>
        <Button variant="secondary" onClick={onClose} disabled={loading}>
          {cancelText}
        </Button>
        <Button
          variant={isDanger ? 'danger' : 'primary'}
          onClick={onConfirm}
          loading={loading}
        >
          {confirmText}
        </Button>
      </div>
    </Modal>
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
