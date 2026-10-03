import React from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  ViewStyle,
  TextStyle,
  ActivityIndicator,
  Modal as RNModal,
  ScrollView,
  KeyboardAvoidingView,
  Platform,
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
// Form Input
// ==========================================
export interface InputProps {
  label: string;
  value: string;
  onChangeText: (text: string) => void;
  placeholder?: string;
  error?: string | null;
  helperText?: string;
  keyboardType?: 'default' | 'numeric' | 'phone-pad' | 'email-address';
  maxLength?: number;
  multiline?: boolean;
  numberOfLines?: number;
  editable?: boolean;
}

export const Input: React.FC<InputProps> = ({
  label,
  value,
  onChangeText,
  placeholder,
  error,
  helperText,
  keyboardType = 'default',
  maxLength,
  multiline,
  numberOfLines,
  editable = true,
}) => (
  <View style={styles.inputContainer}>
    <Text style={styles.inputLabel}>{label}</Text>
    <TextInput
      style={[
        styles.textInput,
        Boolean(error) && styles.textInputError,
        multiline && { height: 70, textAlignVertical: 'top' },
        !editable && { backgroundColor: '#f1f5f9', opacity: 0.7 },
      ]}
      value={value}
      onChangeText={onChangeText}
      placeholder={placeholder}
      placeholderTextColor="#94a3b8"
      keyboardType={keyboardType}
      maxLength={maxLength}
      multiline={multiline}
      numberOfLines={numberOfLines}
      editable={editable}
    />
    {error ? (
      <Text style={styles.inputErrorText}>{error}</Text>
    ) : helperText ? (
      <Text style={styles.inputHelperText}>{helperText}</Text>
    ) : null}
  </View>
);

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
  return (
    <RNModal
      visible={isOpen}
      animationType="slide"
      transparent={true}
      onRequestClose={onClose}
    >
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        style={styles.modalOverlay}
      >
        <TouchableOpacity
          style={styles.modalBackdrop}
          activeOpacity={1}
          onPress={onClose}
        />
        <View style={styles.modalSheet}>
          <View style={styles.modalHeader}>
            <Text style={styles.modalTitle}>{title}</Text>
            <TouchableOpacity onPress={onClose} style={styles.closeBtn}>
              <Text style={styles.closeBtnText}>✕</Text>
            </TouchableOpacity>
          </View>
          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.modalBody}
          >
            {children}
          </ScrollView>
        </View>
      </KeyboardAvoidingView>
    </RNModal>
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
}) => (
  <Modal isOpen={isOpen} onClose={onClose} title={title}>
    <Text style={styles.confirmMessage}>{message}</Text>
    <View style={styles.confirmActions}>
      <Button
        title={cancelText}
        variant="secondary"
        onPress={onClose}
        disabled={loading}
        style={{ flex: 1 }}
      />
      <Button
        title={confirmText}
        variant={isDanger ? 'danger' : 'primary'}
        onPress={onConfirm}
        loading={loading}
        style={{ flex: 1 }}
      />
    </View>
  </Modal>
);

// ==========================================
// Skeleton Placeholder
// ==========================================
export const Skeleton: React.FC<{ height?: number; width?: string | number; borderRadius?: number; style?: ViewStyle }> = ({
  height = 20,
  width = '100%',
  borderRadius = 6,
  style,
}) => (
  <View style={[styles.skeleton, { height, width: width as any, borderRadius }, style]} />
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
  inputContainer: {
    marginBottom: 14,
  },
  inputLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 4,
  },
  textInput: {
    borderWidth: 1,
    borderColor: '#cbd5e1',
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: '#0f172a',
    backgroundColor: '#ffffff',
  },
  textInputError: {
    borderColor: '#dc2626',
  },
  inputErrorText: {
    fontSize: 12,
    color: '#dc2626',
    marginTop: 4,
  },
  inputHelperText: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 4,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.5)',
    justifyContent: 'flex-end',
  },
  modalBackdrop: {
    flex: 1,
  },
  modalSheet: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    maxHeight: '90%',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -4 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 8,
  },
  modalHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 14,
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  closeBtn: {
    padding: 4,
  },
  closeBtnText: {
    fontSize: 18,
    color: '#64748b',
  },
  modalBody: {
    padding: 16,
    paddingBottom: 32,
  },
  confirmMessage: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 20,
    marginBottom: 20,
  },
  confirmActions: {
    flexDirection: 'row',
    gap: 10,
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
