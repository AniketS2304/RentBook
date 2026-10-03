import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
  Modal,
} from 'react-native';
import { AuthProvider, useAuth } from './src/auth/AuthContext';
import { LoginScreen } from './src/screens/LoginScreen';
import { RegisterScreen } from './src/screens/RegisterScreen';
import { DashboardScreen } from './src/screens/DashboardScreen';
import {
  PropertiesScreen,
  TenantsScreen,
  RentScreen,
  PaymentsScreen,
  RemindersScreen,
  ReportsScreen,
  SettingsScreen,
} from './src/screens/PlaceholderScreens';

type PrimaryTab = 'dashboard' | 'properties' | 'tenants' | 'more';
type ActiveView =
  | 'dashboard'
  | 'properties'
  | 'tenants'
  | 'rent'
  | 'payments'
  | 'reminders'
  | 'reports'
  | 'settings';

function MainApp() {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [activeView, setActiveView] = useState<ActiveView>('dashboard');
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState<boolean>(false);

  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2563eb" />
        <Text style={styles.loadingText}>Initializing RentBook...</Text>
      </View>
    );
  }

  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.safeArea}>
        {authView === 'login' ? (
          <LoginScreen onNavigateToRegister={() => setAuthView('register')} />
        ) : (
          <RegisterScreen onNavigateToLogin={() => setAuthView('login')} />
        )}
      </SafeAreaView>
    );
  }

  const handleTabPress = (tab: PrimaryTab) => {
    if (tab === 'more') {
      setIsMoreMenuOpen(true);
    } else {
      setActiveView(tab);
      setIsMoreMenuOpen(false);
    }
  };

  const handleSelectMoreOption = (view: ActiveView) => {
    setActiveView(view);
    setIsMoreMenuOpen(false);
  };

  const isSecondaryView = ['rent', 'payments', 'reminders', 'reports', 'settings'].includes(activeView);

  return (
    <SafeAreaView style={styles.safeArea}>
      {/* App Header */}
      <View style={styles.header}>
        <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
          {isSecondaryView && (
            <TouchableOpacity
              onPress={() => setActiveView('dashboard')}
              style={styles.backBtn}
              accessibilityLabel="Back to Home"
            >
              <Text style={styles.backBtnText}>←</Text>
            </TouchableOpacity>
          )}
          <Text style={styles.headerTitle}>RentBook</Text>
        </View>
        <Text style={styles.headerTag}>{activeView.toUpperCase()}</Text>
      </View>

      {/* Screen Content */}
      <View style={styles.content}>
        {activeView === 'dashboard' && (
          <DashboardScreen onNavigateTab={(tab) => setActiveView(tab as ActiveView)} />
        )}
        {activeView === 'properties' && <PropertiesScreen />}
        {activeView === 'tenants' && <TenantsScreen />}
        {activeView === 'rent' && <RentScreen />}
        {activeView === 'payments' && <PaymentsScreen />}
        {activeView === 'reminders' && <RemindersScreen />}
        {activeView === 'reports' && <ReportsScreen />}
        {activeView === 'settings' && <SettingsScreen />}
      </View>

      {/* Bottom Navigation */}
      <View style={styles.bottomNav}>
        {[
          { tab: 'dashboard', label: 'Home', icon: '🏠' },
          { tab: 'properties', label: 'Properties', icon: '🏢' },
          { tab: 'tenants', label: 'Tenants', icon: '👥' },
          { tab: 'more', label: 'More', icon: '☰' },
        ].map((item) => {
          const isActive =
            item.tab === 'more'
              ? isMoreMenuOpen || isSecondaryView
              : activeView === item.tab && !isMoreMenuOpen;

          return (
            <TouchableOpacity
              key={item.tab}
              onPress={() => handleTabPress(item.tab as PrimaryTab)}
              style={[
                styles.navItem,
                isActive && styles.navItemActive,
              ]}
              accessibilityRole="tab"
              accessibilityState={{ selected: isActive }}
            >
              <Text style={{ fontSize: 16 }}>{item.icon}</Text>
              <Text
                style={[
                  styles.navLabel,
                  isActive && styles.navLabelActive,
                ]}
              >
                {item.label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* More Options Modal Sheet */}
      <Modal
        visible={isMoreMenuOpen}
        animationType="fade"
        transparent={true}
        onRequestClose={() => setIsMoreMenuOpen(false)}
      >
        <TouchableOpacity
          style={styles.modalBackdrop}
          activeOpacity={1}
          onPress={() => setIsMoreMenuOpen(false)}
        >
          <View style={styles.modalContent} onStartShouldSetResponder={() => true}>
            <View style={styles.modalHeader}>
              <Text style={styles.modalTitle}>More Sections</Text>
              <TouchableOpacity onPress={() => setIsMoreMenuOpen(false)}>
                <Text style={styles.modalCloseText}>✕</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.moreOptionsList}>
              {[
                { view: 'rent', label: 'Monthly Rent Register', icon: '📋' },
                { view: 'payments', label: 'Payments History', icon: '💳' },
                { view: 'reminders', label: 'WhatsApp Reminders', icon: '💬' },
                { view: 'reports', label: 'Monthly Summary Reports', icon: '📊' },
                { view: 'settings', label: 'Settings & Profile', icon: '⚙️' },
              ].map((item) => (
                <TouchableOpacity
                  key={item.view}
                  onPress={() => handleSelectMoreOption(item.view as ActiveView)}
                  style={[
                    styles.moreOptionRow,
                    activeView === item.view && styles.moreOptionRowActive,
                  ]}
                >
                  <Text style={{ fontSize: 18 }}>{item.icon}</Text>
                  <Text style={[styles.moreOptionText, activeView === item.view && { color: '#1d4ed8' }]}>
                    {item.label}
                  </Text>
                  <Text style={styles.chevronText}>›</Text>
                </TouchableOpacity>
              ))}

              <TouchableOpacity
                onPress={() => {
                  setIsMoreMenuOpen(false);
                  logout();
                }}
                style={styles.signOutBtn}
              >
                <Text style={{ fontSize: 18 }}>🚪</Text>
                <Text style={styles.signOutText}>Sign Out</Text>
              </TouchableOpacity>
            </View>
          </View>
        </TouchableOpacity>
      </Modal>

      <StatusBar style="dark" />
    </SafeAreaView>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  loadingText: {
    marginTop: 12,
    color: '#64748b',
    fontSize: 14,
  },
  header: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#e2e8f0',
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#ffffff',
  },
  backBtn: {
    paddingRight: 6,
    paddingVertical: 2,
  },
  backBtnText: {
    fontSize: 18,
    color: '#2563eb',
    fontWeight: 'bold',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  headerTag: {
    fontSize: 11,
    fontWeight: 'bold',
    color: '#0369a1',
    backgroundColor: '#e0f2fe',
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 8,
    overflow: 'hidden',
  },
  content: {
    flex: 1,
  },
  bottomNav: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    backgroundColor: '#ffffff',
    paddingVertical: 4,
  },
  navItem: {
    flex: 1,
    paddingVertical: 6,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 52,
  },
  navItemActive: {
    backgroundColor: '#eff6ff',
    borderRadius: 8,
  },
  navLabel: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 2,
  },
  navLabelActive: {
    color: '#2563eb',
    fontWeight: 'bold',
  },
  modalBackdrop: {
    flex: 1,
    backgroundColor: 'rgba(15, 23, 42, 0.5)',
    justifyContent: 'flex-end',
  },
  modalContent: {
    backgroundColor: '#ffffff',
    borderTopLeftRadius: 16,
    borderTopRightRadius: 16,
    paddingHorizontal: 16,
    paddingTop: 16,
    paddingBottom: 32,
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
    marginBottom: 16,
  },
  modalTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  modalCloseText: {
    fontSize: 18,
    color: '#64748b',
    padding: 4,
  },
  moreOptionsList: {
    gap: 8,
  },
  moreOptionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: '#f8fafc',
    gap: 12,
  },
  moreOptionRowActive: {
    backgroundColor: '#eff6ff',
    borderWidth: 1,
    borderColor: '#bfdbfe',
  },
  moreOptionText: {
    flex: 1,
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
  },
  chevronText: {
    fontSize: 16,
    color: '#94a3b8',
  },
  signOutBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 12,
    borderRadius: 10,
    backgroundColor: '#fef2f2',
    marginTop: 6,
    gap: 12,
  },
  signOutText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#dc2626',
  },
});
