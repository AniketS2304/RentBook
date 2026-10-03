import React, { useState } from 'react';
import { AuthProvider, useAuth } from './auth/AuthContext';
import { LoginPage } from './pages/Login';
import { RegisterPage } from './pages/Register';
import { DashboardPage } from './pages/Dashboard';
import { PropertiesPage } from './pages/Properties';
import {
  TenantsPage,
  RentPage,
  PaymentsPage,
  RemindersPage,
  ReportsPage,
  SettingsPage,
} from './pages/Placeholders';

export type PrimaryTab = 'dashboard' | 'properties' | 'tenants' | 'more';
export type ActiveView =
  | 'dashboard'
  | 'properties'
  | 'tenants'
  | 'rent'
  | 'payments'
  | 'reminders'
  | 'reports'
  | 'settings';

const AppContent: React.FC = () => {
  const { isAuthenticated, isLoading, logout } = useAuth();
  const [authView, setAuthView] = useState<'login' | 'register'>('login');
  const [activeView, setActiveView] = useState<ActiveView>('dashboard');
  const [isMoreMenuOpen, setIsMoreMenuOpen] = useState(false);

  if (isLoading) {
    return (
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'center',
          alignItems: 'center',
          height: '100vh',
          fontFamily: 'system-ui, -apple-system, sans-serif',
          backgroundColor: '#f8fafc',
        }}
      >
        <div style={{ fontSize: 32, marginBottom: 12 }}>📖</div>
        <p style={{ color: '#64748b', fontSize: 15, fontWeight: 500 }}>Initializing RentBook...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return (
      <div
        style={{
          fontFamily: 'system-ui, -apple-system, sans-serif',
          minHeight: '100vh',
          background: '#f8fafc',
          padding: 16,
        }}
      >
        {authView === 'login' ? (
          <LoginPage onSwitchToRegister={() => setAuthView('register')} />
        ) : (
          <RegisterPage onSwitchToLogin={() => setAuthView('login')} />
        )}
      </div>
    );
  }

  const handleTabClick = (tab: PrimaryTab) => {
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
    <div
      style={{
        maxWidth: 500,
        margin: '0 auto',
        minHeight: '100vh',
        backgroundColor: '#ffffff',
        fontFamily: 'system-ui, -apple-system, sans-serif',
        display: 'flex',
        flexDirection: 'column',
        boxShadow: '0 0 20px rgba(0,0,0,0.05)',
        position: 'relative',
      }}
    >
      {/* App Header */}
      <header
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid #e2e8f0',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#ffffff',
          position: 'sticky',
          top: 0,
          zIndex: 10,
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          {isSecondaryView && (
            <button
              onClick={() => setActiveView('dashboard')}
              aria-label="Back to dashboard"
              style={{
                background: 'none',
                border: 'none',
                fontSize: 16,
                cursor: 'pointer',
                color: '#2563eb',
                padding: '4px 6px',
                fontWeight: 600,
              }}
            >
              ←
            </button>
          )}
          <span style={{ fontWeight: 800, fontSize: 18, color: '#1e293b', letterSpacing: '-0.02em' }}>
            RentBook
          </span>
        </div>
        <span
          style={{
            fontSize: 11,
            fontWeight: 700,
            textTransform: 'uppercase',
            backgroundColor: '#eff6ff',
            color: '#1d4ed8',
            padding: '3px 8px',
            borderRadius: 9999,
          }}
        >
          {activeView}
        </span>
      </header>

      {/* Main View Area */}
      <main style={{ flex: 1, padding: 16, overflowY: 'auto' }}>
        {activeView === 'dashboard' && <DashboardPage onNavigateTab={(tab) => setActiveView(tab as ActiveView)} />}
        {activeView === 'properties' && <PropertiesPage />}
        {activeView === 'tenants' && <TenantsPage />}
        {activeView === 'rent' && <RentPage />}
        {activeView === 'payments' && <PaymentsPage />}
        {activeView === 'reminders' && <RemindersPage />}
        {activeView === 'reports' && <ReportsPage />}
        {activeView === 'settings' && <SettingsPage />}
      </main>

      {/* Bottom Navigation */}
      <nav
        aria-label="Bottom Navigation"
        style={{
          borderTop: '1px solid #e2e8f0',
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          backgroundColor: '#ffffff',
          position: 'sticky',
          bottom: 0,
          zIndex: 20,
        }}
      >
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
            <button
              key={item.tab}
              onClick={() => handleTabClick(item.tab as PrimaryTab)}
              style={{
                display: 'flex',
                flexDirection: 'column',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '10px 4px',
                border: 'none',
                background: 'transparent',
                cursor: 'pointer',
                color: isActive ? '#2563eb' : '#64748b',
                minHeight: 52,
              }}
            >
              <span style={{ fontSize: 16 }}>{item.icon}</span>
              <span style={{ fontSize: 11, fontWeight: isActive ? 700 : 500, marginTop: 2 }}>
                {item.label}
              </span>
            </button>
          );
        })}
      </nav>

      {/* More Options Modal / Sheet */}
      {isMoreMenuOpen && (
        <div
          role="dialog"
          aria-modal="true"
          aria-label="More Navigation Options"
          style={{
            position: 'fixed',
            inset: 0,
            backgroundColor: 'rgba(15, 23, 42, 0.5)',
            display: 'flex',
            alignItems: 'flex-end',
            justifyContent: 'center',
            zIndex: 100,
          }}
          onClick={() => setIsMoreMenuOpen(false)}
        >
          <div
            style={{
              backgroundColor: '#ffffff',
              width: '100%',
              maxWidth: 500,
              borderTopLeftRadius: 16,
              borderTopRightRadius: 16,
              padding: '20px 16px 32px',
              boxShadow: '0 -4px 20px rgba(0,0,0,0.15)',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#0f172a' }}>More Sections</span>
              <button
                onClick={() => setIsMoreMenuOpen(false)}
                style={{ background: 'none', border: 'none', fontSize: 18, color: '#64748b', cursor: 'pointer' }}
              >
                ✕
              </button>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
              {[
                { view: 'rent', label: 'Monthly Rent Register', icon: '📋' },
                { view: 'payments', label: 'Payments History', icon: '💳' },
                { view: 'reminders', label: 'WhatsApp Reminders', icon: '💬' },
                { view: 'reports', label: 'Monthly Summary Reports', icon: '📊' },
                { view: 'settings', label: 'Settings & Profile', icon: '⚙️' },
              ].map((item) => (
                <button
                  key={item.view}
                  onClick={() => handleSelectMoreOption(item.view as ActiveView)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 12,
                    padding: '12px 14px',
                    borderRadius: 10,
                    border: '1px solid #f1f5f9',
                    backgroundColor: activeView === item.view ? '#eff6ff' : '#f8fafc',
                    color: activeView === item.view ? '#1d4ed8' : '#1e293b',
                    fontSize: 14,
                    fontWeight: 600,
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <span style={{ fontSize: 18 }}>{item.icon}</span>
                  <span style={{ flex: 1 }}>{item.label}</span>
                  <span style={{ color: '#94a3b8' }}>›</span>
                </button>
              ))}

              <button
                onClick={logout}
                style={{
                  marginTop: 8,
                  display: 'flex',
                  alignItems: 'center',
                  gap: 12,
                  padding: '12px 14px',
                  borderRadius: 10,
                  border: '1px solid #fee2e2',
                  backgroundColor: '#fef2f2',
                  color: '#dc2626',
                  fontSize: 14,
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'left',
                }}
              >
                <span style={{ fontSize: 18 }}>🚪</span>
                <span style={{ flex: 1 }}>Sign Out</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export const App: React.FC = () => (
  <AuthProvider>
    <AppContent />
  </AuthProvider>
);

export default App;
