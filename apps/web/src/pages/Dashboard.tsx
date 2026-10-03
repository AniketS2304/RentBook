import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api';
import type {
  DashboardSummaryResponse,
  PropertyListItem,
} from '../types/api';
import {
  formatPaiseToRupees,
  formatIsoDate,
  formatMonthYear,
  getGreeting,
  calculateCollectionPercent,
} from '../utils/format';
import { useAuth } from '../auth/AuthContext';
import {
  Card,
  Badge,
  Button,
  DashboardSkeleton,
  EmptyState,
  ErrorState,
} from '../components/UI';

interface DashboardPageProps {
  onNavigateTab?: (tab: string) => void;
}

export const DashboardPage: React.FC<DashboardPageProps> = ({ onNavigateTab }) => {
  const { user } = useAuth();

  // Current calendar month & year as default
  const today = new Date();
  const [selectedMonth, setSelectedMonth] = useState<number>(today.getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState<number>(today.getFullYear());
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');

  // Data states
  const [properties, setProperties] = useState<PropertyListItem[]>([]);
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [reminderToast, setReminderToast] = useState<string | null>(null);

  // Fetch properties once for property filter
  useEffect(() => {
    api.properties
      .list({ per_page: 100 })
      .then((res) => setProperties(res.items))
      .catch(() => {});
  }, []);

  // Fetch dashboard summary
  const fetchDashboard = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.dashboard.getSummary({
        month: selectedMonth,
        year: selectedYear,
        property_id: selectedPropertyId || undefined,
      });
      setData(res);
    } catch (err: any) {
      setError(err.message || "Couldn't load your dashboard.");
    } finally {
      setLoading(false);
    }
  }, [selectedMonth, selectedYear, selectedPropertyId]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  // Month navigation handlers
  const handlePrevMonth = () => {
    if (selectedMonth === 1) {
      setSelectedMonth(12);
      setSelectedYear((y) => y - 1);
    } else {
      setSelectedMonth((m) => m - 1);
    }
  };

  const handleNextMonth = () => {
    if (selectedMonth === 12) {
      setSelectedMonth(1);
      setSelectedYear((y) => y + 1);
    } else {
      setSelectedMonth((m) => m + 1);
    }
  };

  const handleRemindClick = (tenantName: string) => {
    setReminderToast(`WhatsApp reminder template queued for ${tenantName}`);
    setTimeout(() => setReminderToast(null), 3500);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Toast Notification */}
      {reminderToast && (
        <div
          role="status"
          style={{
            position: 'fixed',
            top: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 50,
            background: '#0f172a',
            color: '#ffffff',
            padding: '10px 18px',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 500,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          {reminderToast}
        </div>
      )}

      {/* Greeting & Header */}
      <div>
        <h1 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a', margin: 0 }}>
          {getGreeting()}, {user?.full_name ? user.full_name.split(' ')[0] : 'Landlord'}
        </h1>
        <p style={{ fontSize: 13, color: '#64748b', margin: '2px 0 0 0' }}>
          Rent register overview
        </p>
      </div>

      {/* Month Selector & Property Filter */}
      <Card style={{ padding: 12 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
          <button
            onClick={handlePrevMonth}
            aria-label="Previous month"
            style={{
              background: '#f1f5f9',
              border: 'none',
              borderRadius: 6,
              width: 34,
              height: 34,
              fontSize: 16,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#334155',
            }}
          >
            ‹
          </button>
          <span style={{ fontWeight: 700, fontSize: 15, color: '#1e293b' }}>
            {formatMonthYear(selectedMonth, selectedYear)}
          </span>
          <button
            onClick={handleNextMonth}
            aria-label="Next month"
            style={{
              background: '#f1f5f9',
              border: 'none',
              borderRadius: 6,
              width: 34,
              height: 34,
              fontSize: 16,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#334155',
            }}
          >
            ›
          </button>
        </div>

        {properties.length > 0 && (
          <div style={{ borderTop: '1px solid #f1f5f9', paddingTop: 8 }}>
            <label htmlFor="property-filter" style={{ fontSize: 12, color: '#64748b', display: 'block', marginBottom: 4 }}>
              Filter by property:
            </label>
            <select
              id="property-filter"
              value={selectedPropertyId}
              onChange={(e) => setSelectedPropertyId(e.target.value)}
              style={{
                width: '100%',
                padding: '6px 10px',
                borderRadius: 6,
                border: '1px solid #cbd5e1',
                fontSize: 13,
                backgroundColor: '#ffffff',
                color: '#1e293b',
              }}
            >
              <option value="">All properties ({properties.length})</option>
              {properties.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </Card>

      {/* Loading Skeleton */}
      {loading && <DashboardSkeleton />}

      {/* Error State */}
      {error && !loading && (
        <ErrorState message={error} onRetry={fetchDashboard} />
      )}

      {/* Empty State for Brand New Landlords */}
      {!loading && !error && data && data.total_units === 0 && data.total_expected_paise === 0 && (
        <EmptyState
          title="Welcome to RentBook 👋"
          description="Add your first property to start tracking rent, units, and tenant collections."
          actionLabel="Add Property"
          onAction={() => onNavigateTab && onNavigateTab('properties')}
        />
      )}

      {/* Dashboard Main Content */}
      {!loading && !error && data && (data.total_units > 0 || data.total_expected_paise > 0) && (
        <>
          {/* Primary Financial Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8 }}>
            {/* Expected */}
            <div
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
                borderRadius: 10,
                padding: '12px 10px',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 600, color: '#64748b', textTransform: 'uppercase' }}>
                Expected
              </span>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', marginTop: 4, wordBreak: 'break-word' }}>
                {formatPaiseToRupees(data.total_expected_paise)}
              </span>
            </div>

            {/* Collected */}
            <div
              style={{
                backgroundColor: '#f0fdf4',
                border: '1px solid #bbf7d0',
                borderRadius: 10,
                padding: '12px 10px',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 600, color: '#16a34a', textTransform: 'uppercase' }}>
                Collected
              </span>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#15803d', marginTop: 4, wordBreak: 'break-word' }}>
                {formatPaiseToRupees(data.total_collected_paise)}
              </span>
            </div>

            {/* Pending */}
            <div
              style={{
                backgroundColor: '#fef2f2',
                border: '1px solid #fecaca',
                borderRadius: 10,
                padding: '12px 10px',
                display: 'flex',
                flexDirection: 'column',
              }}
            >
              <span style={{ fontSize: 11, fontWeight: 600, color: '#dc2626', textTransform: 'uppercase' }}>
                Pending
              </span>
              <span style={{ fontSize: 16, fontWeight: 700, color: '#b91c1c', marginTop: 4, wordBreak: 'break-word' }}>
                {formatPaiseToRupees(data.total_pending_paise)}
              </span>
            </div>
          </div>

          {/* Collection Progress Bar */}
          <Card style={{ padding: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: 13, marginBottom: 8 }}>
              <span style={{ fontWeight: 600, color: '#334155' }}>Collection Progress</span>
              <span style={{ color: '#64748b', fontSize: 12 }}>
                {formatPaiseToRupees(data.total_collected_paise)} of {formatPaiseToRupees(data.total_expected_paise)} ({calculateCollectionPercent(data.total_collected_paise, data.total_expected_paise)}%)
              </span>
            </div>
            <div
              style={{
                height: 10,
                backgroundColor: '#f1f5f9',
                borderRadius: 9999,
                overflow: 'hidden',
                position: 'relative',
              }}
            >
              <div
                style={{
                  height: '100%',
                  width: `${Math.min(100, calculateCollectionPercent(data.total_collected_paise, data.total_expected_paise))}%`,
                  backgroundColor:
                    data.total_expected_paise > 0 && data.total_collected_paise >= data.total_expected_paise
                      ? '#16a34a'
                      : '#2563eb',
                  borderRadius: 9999,
                  transition: 'width 0.3s ease',
                }}
              />
            </div>
          </Card>

          {/* Rent Status Counts & Occupancy */}
          <Card style={{ padding: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <span style={{ fontSize: 13, fontWeight: 600, color: '#1e293b' }}>Rent Records Status</span>
              <span style={{ fontSize: 12, color: '#64748b' }}>
                Occupancy: {data.occupied_units}/{data.total_units} units
              </span>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, textAlign: 'center' }}>
              <div style={{ backgroundColor: '#f0fdf4', padding: '8px 4px', borderRadius: 8, border: '1px solid #bbf7d0' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#15803d' }}>PAID</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#14532d' }}>{data.paid_count}</div>
              </div>
              <div style={{ backgroundColor: '#fef3c7', padding: '8px 4px', borderRadius: 8, border: '1px solid #fde68a' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#b45309' }}>DUE</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#78350f' }}>{data.due_count}</div>
              </div>
              <div style={{ backgroundColor: '#fee2e2', padding: '8px 4px', borderRadius: 8, border: '1px solid #fecaca' }}>
                <div style={{ fontSize: 11, fontWeight: 600, color: '#b91c1c' }}>OVERDUE</div>
                <div style={{ fontSize: 18, fontWeight: 700, color: '#7f1d1d' }}>{data.overdue_count}</div>
              </div>
            </div>
          </Card>

          {/* Today's Due Section */}
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', margin: 0 }}>
                Today's Due ({data.todays_due.length})
              </h2>
            </div>
            {data.todays_due.length === 0 ? (
              <p style={{ fontSize: 13, color: '#16a34a', margin: '4px 0 0', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>✓</span> No rent due today
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {data.todays_due.map((item, idx) => (
                  <div
                    key={item.rent_record_id || idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 0',
                      borderBottom: idx !== data.todays_due.length - 1 ? '1px solid #f1f5f9' : 'none',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>{item.tenant_name}</div>
                      <div style={{ fontSize: 12, color: '#64748b' }}>
                        {item.unit_name} · {item.property_name}
                      </div>
                    </div>
                    <div style={{ textAlign: 'right', display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 700, fontSize: 14, color: '#0f172a' }}>
                        {formatPaiseToRupees(item.amount_paise)}
                      </span>
                      <Button
                        size="sm"
                        variant="secondary"
                        onClick={() => handleRemindClick(item.tenant_name)}
                        style={{ padding: '4px 8px', fontSize: 12 }}
                      >
                        Remind
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Overdue Section */}
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700, color: '#b91c1c', margin: 0 }}>
                Overdue Attention ({data.overdue_list.length})
              </h2>
              {data.overdue_list.length > 0 && onNavigateTab && (
                <button
                  onClick={() => onNavigateTab('rent')}
                  style={{ background: 'none', border: 'none', color: '#2563eb', fontSize: 12, fontWeight: 600, cursor: 'pointer' }}
                >
                  View register →
                </button>
              )}
            </div>
            {data.overdue_list.length === 0 ? (
              <p style={{ fontSize: 13, color: '#16a34a', margin: '4px 0 0', display: 'flex', alignItems: 'center', gap: 6 }}>
                <span>✓</span> No overdue rent
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {data.overdue_list.slice(0, 5).map((item, idx) => (
                  <div
                    key={item.rent_record_id || idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 0',
                      borderBottom: idx !== Math.min(data.overdue_list.length, 5) - 1 ? '1px solid #f1f5f9' : 'none',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>{item.tenant_name}</div>
                      <div style={{ fontSize: 12, color: '#64748b' }}>
                        {item.unit_name} · <span style={{ color: '#b91c1c', fontWeight: 500 }}>{item.days_overdue ?? 1}d overdue</span>
                      </div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontWeight: 700, fontSize: 14, color: '#b91c1c' }}>
                        {formatPaiseToRupees(item.amount_paise)}
                      </div>
                      <span style={{ fontSize: 11, color: '#64748b' }}>remaining balance</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Recent Payments Section */}
          <Card>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <h2 style={{ fontSize: 15, fontWeight: 700, color: '#0f172a', margin: 0 }}>
                Recent Payments ({data.recent_payments.length})
              </h2>
            </div>
            {data.recent_payments.length === 0 ? (
              <p style={{ fontSize: 13, color: '#64748b', margin: '4px 0 0' }}>
                No payments recorded yet for this period.
              </p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                {data.recent_payments.map((p, idx) => (
                  <div
                    key={p.id || idx}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '8px 0',
                      borderBottom: idx !== data.recent_payments.length - 1 ? '1px solid #f1f5f9' : 'none',
                    }}
                  >
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 14, color: '#1e293b' }}>{p.tenant_name}</div>
                      <div style={{ fontSize: 12, color: '#64748b', display: 'flex', alignItems: 'center', gap: 6, marginTop: 2 }}>
                        <Badge status={p.payment_method} label={p.payment_method} />
                        <span>· {formatIsoDate(p.paid_date)}</span>
                      </div>
                    </div>
                    <div style={{ fontWeight: 700, fontSize: 15, color: '#15803d' }}>
                      +{formatPaiseToRupees(p.amount_paise)}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </>
      )}
    </div>
  );
};
