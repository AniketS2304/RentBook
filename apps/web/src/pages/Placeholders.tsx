import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { PropertyListItem, TenantListItem, RentRecordListItem } from '../types/api';
import { formatPaiseToRupees } from '../utils/format';
import { useAuth } from '../auth/AuthContext';

export const PropertiesPage: React.FC = () => {
  const [properties, setProperties] = useState<PropertyListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.properties
      .list()
      .then((res) => setProperties(res.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 12 }}>Properties</h2>
      {loading ? (
        <p>Loading properties...</p>
      ) : properties.length === 0 ? (
        <p style={{ color: '#64748b' }}>No properties added yet.</p>
      ) : (
        <ul>
          {properties.map((p) => (
            <li key={p.id}>
              {p.name} ({p.unit_count} units, {p.occupied_count} occupied)
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export const TenantsPage: React.FC = () => {
  const [tenants, setTenants] = useState<TenantListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.tenants
      .list()
      .then((res) => setTenants(res.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 12 }}>Tenants</h2>
      {loading ? (
        <p>Loading tenants...</p>
      ) : tenants.length === 0 ? (
        <p style={{ color: '#64748b' }}>No tenants registered yet.</p>
      ) : (
        <ul>
          {tenants.map((t) => (
            <li key={t.id}>
              {t.name} - {t.unit.name} ({t.status})
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export const RentPage: React.FC = () => {
  const [records, setRecords] = useState<RentRecordListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const now = new Date();
    api.rent
      .list({ month: now.getMonth() + 1, year: now.getFullYear() })
      .then((res) => setRecords(res.items))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 12 }}>Rent Register</h2>
      {loading ? (
        <p>Loading monthly rent register...</p>
      ) : records.length === 0 ? (
        <p style={{ color: '#64748b' }}>No rent records for current month.</p>
      ) : (
        <ul>
          {records.map((r) => (
            <li key={r.id}>
              {r.tenant_name} ({r.unit_name}): {formatPaiseToRupees(r.expected_amount_paise)} - [{r.status}]
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export const PaymentsPage: React.FC = () => (
  <div>
    <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 12 }}>Payments</h2>
    <p style={{ color: '#64748b' }}>Payment recording foundation initialized.</p>
  </div>
);

export const RemindersPage: React.FC = () => (
  <div>
    <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 12 }}>Reminders</h2>
    <p style={{ color: '#64748b' }}>WhatsApp reminder foundation initialized.</p>
  </div>
);

export const ReportsPage: React.FC = () => (
  <div>
    <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 12 }}>Monthly Reports</h2>
    <p style={{ color: '#64748b' }}>Monthly collection report foundation initialized.</p>
  </div>
);

export const SettingsPage: React.FC = () => {
  const { user, logout } = useAuth();
  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 12 }}>Settings & Profile</h2>
      <p><strong>Name:</strong> {user?.full_name}</p>
      <p><strong>Email:</strong> {user?.email}</p>
      <button
        onClick={logout}
        style={{
          marginTop: 16,
          padding: '8px 16px',
          background: '#dc2626',
          color: 'white',
          border: 'none',
          borderRadius: 6,
          cursor: 'pointer',
        }}
      >
        Sign Out
      </button>
    </div>
  );
};
