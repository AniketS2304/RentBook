import React, { useState } from 'react';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { LoginPage } from './pages/Login';
import { RegisterPage } from './pages/Register';
import { DashboardPage } from './pages/Dashboard';
import {
  PropertiesPage,
  TenantsPage,
  RentPage,
  PaymentsPage,
  RemindersPage,
  ReportsPage,
  SettingsPage,
} from './pages/Placeholders';

type Tab =
  | 'dashboard'
  | 'properties'
  | 'tenants'
  | 'rent'
  | 'payments'
  | 'reminders'
  | 'reports'
  | 'settings';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [activeTab, setActiveTab] = useState<Tab>('dashboard');

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', fontFamily: 'sans-serif' }}>
        <p style={{ color: '#64748b' }}>Initializing RentBook...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div style={{ fontFamily: 'sans-serif', minHeight: '100vh', background: '#f8fafc', padding: 16 }}>
        {authView === 'login' ? (
          <LoginPage onSwitchToRegister={() => setAuthView('register')} />
        ) : (
          <RegisterPage onSwitchToLogin={() => setAuthView('login')} />
        )}
      </div>
    );
  }

  return (
    <div style={{ maxWidth: 500, margin: '0 auto', minHeight: '100vh', background: '#ffffff', fontFamily: 'sans-serif', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <header style={{ padding: '12px 16px', borderBottom: '1px solid #e2e8f0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <span style={{ fontWeight: 'bold', fontSize: 18, color: '#1e293b' }}>RentBook</span>
        <span style={{ fontSize: 12, background: '#e0f2fe', color: '#0369a1', padding: '2px 8px', borderRadius: 12 }}>
          {activeTab.toUpperCase()}
        </span>
      </header>

      {/* Main Content Area */}
      <main style={{ flex: 1, padding: 16, overflowY: 'auto' }}>
        {activeTab === 'dashboard' && <DashboardPage />}
        {activeTab === 'properties' && <PropertiesPage />}
        {activeTab === 'tenants' && <TenantsPage />}
        {activeTab === 'rent' && <RentPage />}
        {activeTab === 'payments' && <PaymentsPage />}
        {activeTab === 'reminders' && <RemindersPage />}
        {activeTab === 'reports' && <ReportsPage />}
        {activeTab === 'settings' && <SettingsPage />}
      </main>

      {/* Navigation Bar */}
      <nav style={{ borderTop: '1px solid #e2e8f0', display: 'flex', flexWrap: 'wrap', background: '#f8fafc', padding: 4 }}>
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
          <button
            key={item.tab}
            onClick={() => setActiveTab(item.tab as Tab)}
            style={{
              flex: '1 0 25%',
              padding: '8px 4px',
              border: 'none',
              background: activeTab === item.tab ? '#e2e8f0' : 'transparent',
              fontWeight: activeTab === item.tab ? 'bold' : 'normal',
              color: activeTab === item.tab ? '#1d4ed8' : '#64748b',
              fontSize: 12,
              cursor: 'pointer',
              borderRadius: 4,
            }}
          >
            {item.label}
          </button>
        ))}
      </nav>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
};

export default App;
