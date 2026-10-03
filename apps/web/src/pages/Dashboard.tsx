import React, { useEffect, useState } from 'react';
import { api } from '../api';
import type { DashboardSummaryResponse } from '../types/api';
import { formatPaiseToRupees } from '../utils/format';
import { useAuth } from '../auth/AuthContext';

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    const fetchDashboard = async () => {
      try {
        setLoading(true);
        const res = await api.dashboard.getSummary();
        if (active) setData(res);
      } catch (err: any) {
        if (active) setError(err.message || 'Failed to load dashboard');
      } finally {
        if (active) setLoading(false);
      }
    };
    fetchDashboard();
    return () => {
      active = false;
    };
  }, []);

  return (
    <div>
      <h2 style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 8 }}>
        Welcome, {user?.full_name || 'Landlord'}
      </h2>
      <p style={{ color: '#64748b', marginBottom: 16 }}>
        Dashboard Summary & Overdue Overview
      </p>

      {loading && <div>Loading dashboard data...</div>}
      {error && <div style={{ color: '#dc2626' }}>Error: {error}</div>}

      {data && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 12, marginBottom: 16 }}>
            <div style={{ background: '#f8fafc', padding: 12, borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: 12, color: '#64748b' }}>Expected</div>
              <div style={{ fontSize: 18, fontWeight: 'bold' }}>{formatPaiseToRupees(data.total_expected_paise)}</div>
            </div>
            <div style={{ background: '#f0fdf4', padding: 12, borderRadius: 8, border: '1px solid #bbf7d0' }}>
              <div style={{ fontSize: 12, color: '#16a34a' }}>Collected</div>
              <div style={{ fontSize: 18, fontWeight: 'bold', color: '#15803d' }}>{formatPaiseToRupees(data.total_collected_paise)}</div>
            </div>
            <div style={{ background: '#fef2f2', padding: 12, borderRadius: 8, border: '1px solid #fecaca' }}>
              <div style={{ fontSize: 12, color: '#dc2626' }}>Pending</div>
              <div style={{ fontSize: 18, fontWeight: 'bold', color: '#b91c1c' }}>{formatPaiseToRupees(data.total_pending_paise)}</div>
            </div>
          </div>
          <div style={{ fontSize: 14, color: '#475569' }}>
            Occupancy: {data.occupied_units} / {data.total_units} units occupied ({data.vacant_units} vacant)
          </div>
        </div>
      )}
    </div>
  );
};
