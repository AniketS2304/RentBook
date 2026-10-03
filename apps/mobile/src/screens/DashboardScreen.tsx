import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ActivityIndicator,
  ScrollView,
} from 'react-native';
import { api } from '../api';
import type { DashboardSummaryResponse } from '../types/api';
import { formatPaiseToRupees } from '../utils/format';
import { useAuth } from '../auth/AuthContext';

export const DashboardScreen: React.FC = () => {
  const { user } = useAuth();
  const [data, setData] = useState<DashboardSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.dashboard
      .getSummary()
      .then((res) => {
        if (active) setData(res);
      })
      .catch((err: any) => {
        if (active) setError(err.message || 'Failed to load dashboard');
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.greeting}>Welcome, {user?.full_name || 'Landlord'}</Text>
      <Text style={styles.subtitle}>Overview of current month collections</Text>

      {loading && (
        <View style={styles.centerBox}>
          <ActivityIndicator size="small" color="#2563eb" />
          <Text style={styles.loadingText}>Fetching collections...</Text>
        </View>
      )}

      {error && (
        <View style={styles.errorBox}>
          <Text style={styles.errorText}>Error: {error}</Text>
        </View>
      )}

      {data && (
        <View style={styles.cardsRow}>
          <View style={[styles.card, styles.cardExpected]}>
            <Text style={styles.cardLabel}>Expected</Text>
            <Text style={styles.cardValue}>
              {formatPaiseToRupees(data.total_expected_paise)}
            </Text>
          </View>
          <View style={[styles.card, styles.cardCollected]}>
            <Text style={[styles.cardLabel, { color: '#16a34a' }]}>Collected</Text>
            <Text style={[styles.cardValue, { color: '#15803d' }]}>
              {formatPaiseToRupees(data.total_collected_paise)}
            </Text>
          </View>
          <View style={[styles.card, styles.cardPending]}>
            <Text style={[styles.cardLabel, { color: '#dc2626' }]}>Pending</Text>
            <Text style={[styles.cardValue, { color: '#b91c1c' }]}>
              {formatPaiseToRupees(data.total_pending_paise)}
            </Text>
          </View>
        </View>
      )}

      {data && (
        <View style={styles.infoBox}>
          <Text style={styles.infoText}>
            Occupancy: {data.occupied_units} / {data.total_units} units occupied ({data.vacant_units} vacant)
          </Text>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    padding: 16,
    flexGrow: 1,
  },
  greeting: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  subtitle: {
    fontSize: 13,
    color: '#64748b',
    marginBottom: 16,
  },
  centerBox: {
    padding: 24,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 8,
    color: '#64748b',
    fontSize: 13,
  },
  errorBox: {
    padding: 12,
    backgroundColor: '#fee2e2',
    borderRadius: 8,
    marginBottom: 16,
  },
  errorText: {
    color: '#991b1b',
    fontSize: 13,
  },
  cardsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  card: {
    flex: 1,
    padding: 12,
    borderRadius: 8,
    marginHorizontal: 4,
    borderWidth: 1,
  },
  cardExpected: {
    backgroundColor: '#f8fafc',
    borderColor: '#e2e8f0',
  },
  cardCollected: {
    backgroundColor: '#f0fdf4',
    borderColor: '#bbf7d0',
  },
  cardPending: {
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
  },
  cardLabel: {
    fontSize: 11,
    color: '#64748b',
    marginBottom: 4,
  },
  cardValue: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  infoBox: {
    backgroundColor: '#f8fafc',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  infoText: {
    fontSize: 13,
    color: '#475569',
  },
});
