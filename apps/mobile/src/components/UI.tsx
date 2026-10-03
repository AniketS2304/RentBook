import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  ViewStyle,
  TextStyle,
  ActivityIndicator,
} from 'react-native';

// ==========================================
// Card
// ==========================================
export interface CardProps {
  children: React.ReactNode;
  style?: ViewStyle;
}

export const Card: React.FC<CardProps> = ({ children, style }) => (
  <View style={[styles.card, style]}>{children}</View>
);

// ==========================================
// Badge
// ==========================================
export interface BadgeProps {
  status: string;
  label?: string;
  style?: ViewStyle;
}

export const Badge: React.FC<BadgeProps> = ({ status, label, style }) => {
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
    <View style={[styles.badge, { backgroundColor: bg, borderColor: border }, style]}>
      <Text style={[styles.badgeText, { color }]}>
        {label || normalized.replace('_', ' ')}
      </Text>
    </View>
  );
};

// ==========================================
// Button
// ==========================================
export interface ButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'outline' | 'danger';
  size?: 'sm' | 'md' | 'lg';
  disabled?: boolean;
  loading?: boolean;
  style?: ViewStyle;
  textStyle?: TextStyle;
}

export const Button: React.FC<ButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  style,
  textStyle,
}) => {
  let bg = '#2563eb';
  let color = '#ffffff';
  let border = 'transparent';

  if (variant === 'secondary') {
    bg = '#f1f5f9';
    color = '#1e293b';
  } else if (variant === 'outline') {
    bg = 'transparent';
    color = '#2563eb';
    border = '#2563eb';
  } else if (variant === 'danger') {
    bg = '#dc2626';
    color = '#ffffff';
  }

  const height = size === 'sm' ? 36 : size === 'lg' ? 50 : 44;
  const paddingH = size === 'sm' ? 12 : size === 'lg' ? 24 : 16;
  const fontSize = size === 'sm' ? 13 : 15;

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled || loading}
      activeOpacity={0.7}
      style={[
        styles.button,
        {
          backgroundColor: bg,
          borderColor: border,
          borderWidth: variant === 'outline' ? 1 : 0,
          height,
          paddingHorizontal: paddingH,
          opacity: disabled ? 0.6 : 1,
        },
        style,
      ]}
    >
      {loading ? (
        <ActivityIndicator color={color} size="small" />
      ) : (
        <Text style={[styles.buttonText, { color, fontSize }, textStyle]}>{title}</Text>
      )}
    </TouchableOpacity>
  );
};

// ==========================================
// Skeleton Placeholder
// ==========================================
export const Skeleton: React.FC<{ height?: number; width?: string | number; style?: ViewStyle }> = ({
  height = 20,
  width = '100%',
  style,
}) => (
  <View style={[styles.skeleton, { height, width: width as any }, style]} />
);

export const DashboardSkeleton: React.FC = () => (
  <View style={{ gap: 14 }}>
    <View style={{ flexDirection: 'row', justifyContent: 'space-between' }}>
      <Skeleton height={28} width="55%" />
      <Skeleton height={28} width="35%" />
    </View>
    <View style={{ flexDirection: 'row', gap: 8 }}>
      <Skeleton height={74} width="31%" />
      <Skeleton height={74} width="31%" />
      <Skeleton height={74} width="31%" />
    </View>
    <Skeleton height={60} />
    <Skeleton height={120} />
    <Skeleton height={120} />
  </View>
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
  <Card style={styles.emptyContainer}>
    <Text style={styles.emptyIcon}>{icon}</Text>
    <Text style={styles.emptyTitle}>{title}</Text>
    <Text style={styles.emptyDesc}>{description}</Text>
    {actionLabel && onAction && (
      <Button title={actionLabel} onPress={onAction} style={{ marginTop: 12 }} />
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
  <Card style={styles.errorContainer}>
    <Text style={styles.errorIcon}>⚠️</Text>
    <Text style={styles.errorMsg}>{message}</Text>
    <Button title="Retry" onPress={onRetry} variant="outline" size="sm" style={{ borderColor: '#dc2626' }} textStyle={{ color: '#dc2626' }} />
  </Card>
);

const styles = StyleSheet.create({
  card: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e2e8f0',
    borderRadius: 12,
    padding: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  badge: {
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 999,
    borderWidth: 1,
    alignSelf: 'flex-start',
  },
  badgeText: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 0.5,
  },
  button: {
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  buttonText: {
    fontWeight: 'bold',
  },
  skeleton: {
    backgroundColor: '#f1f5f9',
    borderRadius: 6,
  },
  emptyContainer: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 16,
  },
  emptyIcon: {
    fontSize: 36,
    marginBottom: 8,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#0f172a',
    textAlign: 'center',
  },
  emptyDesc: {
    fontSize: 14,
    color: '#64748b',
    textAlign: 'center',
    marginTop: 6,
    marginBottom: 16,
    maxWidth: 280,
    lineHeight: 20,
  },
  errorContainer: {
    alignItems: 'center',
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
    paddingVertical: 20,
  },
  errorIcon: {
    fontSize: 28,
    marginBottom: 6,
  },
  errorMsg: {
    fontSize: 14,
    fontWeight: '600',
    color: '#991b1b',
    marginBottom: 12,
    textAlign: 'center',
  },
});
