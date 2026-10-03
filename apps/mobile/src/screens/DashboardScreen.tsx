import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
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

interface DashboardScreenProps {
  onNavigateTab?: (tab: string) => void;
}

export const DashboardScreen: React.FC<DashboardScreenProps> = ({ onNavigateTab }) => {
  const { user } = useAuth();

  const today = new Date();
  const [selectedMonth, setSelectedMonth] = useState<number>(today.getMonth() + 1);
  const [selectedYear, setSelectedYear] = useState<number>(today.getFullYear());
  const [selectedPropertyId, setSelectedPropertyId] = useState<string>('');

  const [properties, setProperties] = useState<PropertyListItem[]>([]);
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Load properties for filtering
  useEffect(() => {
    api.properties
      .list({ per_page: 100 })
      .then((res) => setProperties(res.items))
      .catch(() => {});
  }, []);

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

  const handleRemindPress = (tenantName: string) => {
    Alert.alert(
      'WhatsApp Reminder',
      `WhatsApp reminder template prepared for ${tenantName}. Direct reminder generation is enabled in the Reminders tab.`,
      [{ text: 'OK' }]
    );
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* Greeting Header */}
      <View style={styles.headerBox}>
        <Text style={styles.greeting}>
          {getGreeting()}, {user?.full_name ? user.full_name.split(' ')[0] : 'Landlord'}
        </Text>
        <Text style={styles.headerSubtitle}>Rent register overview</Text>
      </View>

      {/* Month Navigation & Property Filter */}
      <Card style={styles.filterCard}>
        <View style={styles.monthRow}>
          <TouchableOpacity
            onPress={handlePrevMonth}
            style={styles.monthArrowBtn}
            accessibilityLabel="Previous month"
          >
            <Text style={styles.arrowText}>‹</Text>
          </TouchableOpacity>
          <Text style={styles.monthTitle}>
            {formatMonthYear(selectedMonth, selectedYear)}
          </Text>
          <TouchableOpacity
            onPress={handleNextMonth}
            style={styles.monthArrowBtn}
            accessibilityLabel="Next month"
          >
            <Text style={styles.arrowText}>›</Text>
          </TouchableOpacity>
        </View>

        {properties.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.propertyScroll}
          >
            <TouchableOpacity
              onPress={() => setSelectedPropertyId('')}
              style={[
                styles.propertyChip,
                selectedPropertyId === '' && styles.propertyChipActive,
              ]}
            >
              <Text
                style={[
                  styles.propertyChipText,
                  selectedPropertyId === '' && styles.propertyChipTextActive,
                ]}
              >
                All ({properties.length})
              </Text>
            </TouchableOpacity>
            {properties.map((p) => (
              <TouchableOpacity
                key={p.id}
                onPress={() => setSelectedPropertyId(p.id)}
                style={[
                  styles.propertyChip,
                  selectedPropertyId === p.id && styles.propertyChipActive,
                ]}
              >
                <Text
                  style={[
                    styles.propertyChipText,
                    selectedPropertyId === p.id && styles.propertyChipTextActive,
                  ]}
                  numberOfLines={1}
                >
                  {p.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        )}
      </Card>

      {/* Loading Skeleton */}
      {loading && <DashboardSkeleton />}

      {/* Error View */}
      {error && !loading && (
        <ErrorState message={error} onRetry={fetchDashboard} />
      )}

      {/* Empty State for New Landlord */}
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
        <View style={styles.contentColumn}>
          {/* Primary Financial Cards */}
          <View style={styles.financialRow}>
            {/* Expected */}
            <View style={[styles.finCard, styles.finCardExpected]}>
              <Text style={styles.finLabel}>Expected</Text>
              <Text style={styles.finValue}>
                {formatPaiseToRupees(data.total_expected_paise)}
              </Text>
            </View>

            {/* Collected */}
            <View style={[styles.finCard, styles.finCardCollected]}>
              <Text style={[styles.finLabel, { color: '#16a34a' }]}>Collected</Text>
              <Text style={[styles.finValue, { color: '#15803d' }]}>
                {formatPaiseToRupees(data.total_collected_paise)}
              </Text>
            </View>

            {/* Pending */}
            <View style={[styles.finCard, styles.finCardPending]}>
              <Text style={[styles.finLabel, { color: '#dc2626' }]}>Pending</Text>
              <Text style={[styles.finValue, { color: '#b91c1c' }]}>
                {formatPaiseToRupees(data.total_pending_paise)}
              </Text>
            </View>
          </View>

          {/* Collection Progress */}
          <Card style={styles.progressCard}>
            <View style={styles.progressHeader}>
              <Text style={styles.progressTitle}>Collection Progress</Text>
              <Text style={styles.progressSubtitle}>
                {calculateCollectionPercent(data.total_collected_paise, data.total_expected_paise)}% (
                {formatPaiseToRupees(data.total_collected_paise)} of{' '}
                {formatPaiseToRupees(data.total_expected_paise)})
              </Text>
            </View>
            <View style={styles.progressBarTrack}>
              <View
                style={[
                  styles.progressBarFill,
                  {
                    width: `${Math.min(
                      100,
                      calculateCollectionPercent(
                        data.total_collected_paise,
                        data.total_expected_paise
                      )
                    )}%`,
                    backgroundColor:
                      data.total_expected_paise > 0 &&
                      data.total_collected_paise >= data.total_expected_paise
                        ? '#16a34a'
                        : '#2563eb',
                  },
                ]}
              />
            </View>
          </Card>

          {/* Status Breakdown & Occupancy */}
          <Card style={styles.statusCard}>
            <View style={styles.statusHeader}>
              <Text style={styles.statusSectionTitle}>Rent Status</Text>
              <Text style={styles.occupancyText}>
                Occupancy: {data.occupied_units}/{data.total_units} units
              </Text>
            </View>
            <View style={styles.statusRow}>
              <View style={[styles.statusBox, { backgroundColor: '#f0fdf4', borderColor: '#bbf7d0' }]}>
                <Text style={[styles.statusBoxLabel, { color: '#15803d' }]}>PAID</Text>
                <Text style={[styles.statusBoxCount, { color: '#14532d' }]}>{data.paid_count}</Text>
              </View>
              <View style={[styles.statusBox, { backgroundColor: '#fef3c7', borderColor: '#fde68a' }]}>
                <Text style={[styles.statusBoxLabel, { color: '#b45309' }]}>DUE</Text>
                <Text style={[styles.statusBoxCount, { color: '#78350f' }]}>{data.due_count}</Text>
              </View>
              <View style={[styles.statusBox, { backgroundColor: '#fee2e2', borderColor: '#fecaca' }]}>
                <Text style={[styles.statusBoxLabel, { color: '#b91c1c' }]}>OVERDUE</Text>
                <Text style={[styles.statusBoxCount, { color: '#7f1d1d' }]}>{data.overdue_count}</Text>
              </View>
            </View>
          </Card>

          {/* Today's Due Section */}
          <Card>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Today's Due ({data.todays_due.length})
              </Text>
            </View>
            {data.todays_due.length === 0 ? (
              <Text style={styles.greenCheckText}>✓ No rent due today</Text>
            ) : (
              <View style={styles.itemsList}>
                {data.todays_due.map((item, idx) => (
                  <View
                    key={item.rent_record_id || idx}
                    style={[
                      styles.listItemRow,
                      idx !== data.todays_due.length - 1 && styles.borderBottom,
                    ]}
                  >
                    <View style={{ flex: 1 }}>
                      <Text style={styles.itemTitle}>{item.tenant_name}</Text>
                      <Text style={styles.itemSubtitle}>
                        {item.unit_name} · {item.property_name}
                      </Text>
                    </View>
                    <View style={styles.actionCol}>
                      <Text style={styles.itemAmount}>
                        {formatPaiseToRupees(item.amount_paise)}
                      </Text>
                      <Button
                        title="Remind"
                        size="sm"
                        variant="secondary"
                        onPress={() => handleRemindPress(item.tenant_name)}
                        style={{ height: 32, paddingHorizontal: 10, marginTop: 4 }}
                        textStyle={{ fontSize: 12 }}
                      />
                    </View>
                  </View>
                ))}
              </View>
            )}
          </Card>

          {/* Overdue Section */}
          <Card>
            <View style={styles.sectionHeader}>
              <Text style={[styles.sectionTitle, { color: '#b91c1c' }]}>
                Overdue Attention ({data.overdue_list.length})
              </Text>
              {data.overdue_list.length > 0 && onNavigateTab && (
                <TouchableOpacity onPress={() => onNavigateTab('rent')}>
                  <Text style={styles.viewRegisterText}>View register →</Text>
                </TouchableOpacity>
              )}
            </View>
            {data.overdue_list.length === 0 ? (
              <Text style={styles.greenCheckText}>✓ No overdue rent</Text>
            ) : (
              <View style={styles.itemsList}>
                {data.overdue_list.slice(0, 5).map((item, idx) => (
                  <View
                    key={item.rent_record_id || idx}
                    style={[
                      styles.listItemRow,
                      idx !== Math.min(data.overdue_list.length, 5) - 1 && styles.borderBottom,
                    ]}
                  >
                    <View style={{ flex: 1 }}>
                      <Text style={styles.itemTitle}>{item.tenant_name}</Text>
                      <Text style={styles.itemSubtitle}>
                        {item.unit_name} ·{' '}
                        <Text style={{ color: '#b91c1c', fontWeight: 'bold' }}>
                          {item.days_overdue ?? 1}d overdue
                        </Text>
                      </Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                      <Text style={[styles.itemAmount, { color: '#b91c1c' }]}>
                        {formatPaiseToRupees(item.amount_paise)}
                      </Text>
                      <Text style={styles.balanceSub}>remaining balance</Text>
                    </View>
                  </View>
                ))}
              </View>
            )}
          </Card>

          {/* Recent Payments Section */}
          <Card>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>
                Recent Payments ({data.recent_payments.length})
              </Text>
            </View>
            {data.recent_payments.length === 0 ? (
              <Text style={styles.emptyRecentText}>No payments recorded yet for this period.</Text>
            ) : (
              <View style={styles.itemsList}>
                {data.recent_payments.map((p, idx) => (
                  <View
                    key={p.id || idx}
                    style={[
                      styles.listItemRow,
                      idx !== data.recent_payments.length - 1 && styles.borderBottom,
                    ]}
                  >
                    <View style={{ flex: 1 }}>
                      <Text style={styles.itemTitle}>{p.tenant_name}</Text>
                      <View style={styles.paymentMetaRow}>
                        <Badge status={p.payment_method} label={p.payment_method} />
                        <Text style={styles.paymentDateText}>· {formatIsoDate(p.paid_date)}</Text>
                      </View>
                    </View>
                    <Text style={styles.paymentAmount}>
                      +{formatPaiseToRupees(p.amount_paise)}
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </Card>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    flexGrow: 1,
    backgroundColor: '#ffffff',
  },
  headerBox: {
    marginBottom: 12,
  },
  greeting: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  headerSubtitle: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 2,
  },
  filterCard: {
    padding: 10,
    marginBottom: 14,
  },
  monthRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  monthArrowBtn: {
    width: 36,
    height: 36,
    borderRadius: 8,
    backgroundColor: '#f1f5f9',
    alignItems: 'center',
    justifyContent: 'center',
  },
  arrowText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#334155',
  },
  monthTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  propertyScroll: {
    marginTop: 10,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#f1f5f9',
  },
  propertyChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    backgroundColor: '#f1f5f9',
    marginRight: 8,
  },
  propertyChipActive: {
    backgroundColor: '#eff6ff',
    borderWidth: 1,
    borderColor: '#3b82f6',
  },
  propertyChipText: {
    fontSize: 12,
    color: '#475569',
    fontWeight: '500',
  },
  propertyChipTextActive: {
    color: '#1d4ed8',
    fontWeight: 'bold',
  },
  contentColumn: {
    gap: 14,
  },
  financialRow: {
    flexDirection: 'row',
    gap: 8,
  },
  finCard: {
    flex: 1,
    padding: 10,
    borderRadius: 10,
    borderWidth: 1,
  },
  finCardExpected: {
    backgroundColor: '#f8fafc',
    borderColor: '#e2e8f0',
  },
  finCardCollected: {
    backgroundColor: '#f0fdf4',
    borderColor: '#bbf7d0',
  },
  finCardPending: {
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
  },
  finLabel: {
    fontSize: 11,
    fontWeight: '700',
    color: '#64748b',
    textTransform: 'uppercase',
  },
  finValue: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#0f172a',
    marginTop: 4,
  },
  progressCard: {
    padding: 14,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  progressTitle: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
  },
  progressSubtitle: {
    fontSize: 11,
    color: '#64748b',
  },
  progressBarTrack: {
    height: 10,
    backgroundColor: '#f1f5f9',
    borderRadius: 5,
    overflow: 'hidden',
  },
  progressBarFill: {
    height: '100%',
    borderRadius: 5,
  },
  statusCard: {
    padding: 14,
  },
  statusHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 10,
  },
  statusSectionTitle: {
    fontSize: 13,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  occupancyText: {
    fontSize: 12,
    color: '#64748b',
  },
  statusRow: {
    flexDirection: 'row',
    gap: 8,
  },
  statusBox: {
    flex: 1,
    padding: 8,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  statusBoxLabel: {
    fontSize: 10,
    fontWeight: 'bold',
  },
  statusBoxCount: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 2,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  viewRegisterText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2563eb',
  },
  greenCheckText: {
    fontSize: 13,
    color: '#16a34a',
    marginTop: 4,
  },
  emptyRecentText: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
  itemsList: {
    gap: 2,
  },
  listItemRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  borderBottom: {
    borderBottomWidth: 1,
    borderBottomColor: '#f1f5f9',
  },
  itemTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e293b',
  },
  itemSubtitle: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  actionCol: {
    alignItems: 'flex-end',
  },
  itemAmount: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  balanceSub: {
    fontSize: 10,
    color: '#64748b',
  },
  paymentMetaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginTop: 3,
  },
  paymentDateText: {
    fontSize: 12,
    color: '#64748b',
  },
  paymentAmount: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#15803d',
  },
});
