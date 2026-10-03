import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import {
  SafeAreaView,
  StyleSheet,
  Text,
  View,
  TouchableOpacity,
  ActivityIndicator,
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

type Tab =
  | 'dashboard'
  | 'properties'
  | 'tenants'
  | 'rent'
  | 'payments'
  | 'reminders'
  | 'reports'
  | 'settings';

function MainApp() {
  const { isAuthenticated, isLoading } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

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

  return (
    <SafeAreaView style={styles.safeArea}>
      <View style={styles.header}>
        <Text style={styles.headerTitle}>RentBook</Text>
        <Text style={styles.headerTag}>{activeTab.toUpperCase()}</Text>
      </View>

      <View style={styles.content}>
        {activeTab === 'dashboard' && <DashboardScreen />}
        {activeTab === 'properties' && <PropertiesScreen />}
        {activeTab === 'tenants' && <TenantsScreen />}
        {activeTab === 'rent' && <RentScreen />}
        {activeTab === 'payments' && <PaymentsScreen />}
        {activeTab === 'reminders' && <RemindersScreen />}
        {activeTab === 'reports' && <ReportsScreen />}
        {activeTab === 'settings' && <SettingsScreen />}
      </View>

      <View style={styles.bottomNav}>
        {[
          { tab: 'dashboard', label: 'Home' },
          { tab: 'properties', label: 'Props' },
          { tab: 'tenants', label: 'Tenants' },
          { tab: 'rent', label: 'Rent' },
          { tab: 'payments', label: 'Pay' },
          { tab: 'reminders', label: 'Alerts' },
          { tab: 'reports', label: 'Reports' },
          { tab: 'settings', label: 'Profile' },
        ].map((item) => (
          <TouchableOpacity
            key={item.tab}
            onPress={() => setActiveTab(item.tab as Tab)}
            style={[
              styles.navItem,
              activeTab === item.tab && styles.navItemActive,
            ]}
          >
            <Text
              style={[
                styles.navLabel,
                activeTab === item.tab && styles.navLabelActive,
              ]}
            >
              {item.label}
            </Text>
          </TouchableOpacity>
        ))}
      </View>
      <StatusBar style="auto" />
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
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  headerTag: {
    fontSize: 11,
    color: '#0369a1',
    backgroundColor: '#e0f2fe',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
    overflow: 'hidden',
  },
  content: {
    flex: 1,
  },
  bottomNav: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    backgroundColor: '#f8fafc',
    paddingVertical: 4,
  },
  navItem: {
    width: '25%',
    paddingVertical: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  navItemActive: {
    backgroundColor: '#e2e8f0',
    borderRadius: 6,
  },
  navLabel: {
    fontSize: 11,
    color: '#64748b',
  },
  navLabelActive: {
    color: '#2563eb',
    fontWeight: 'bold',
  },
});
