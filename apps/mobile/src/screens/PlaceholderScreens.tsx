import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  ActivityIndicator,
} from 'react-native';
import { api } from '../api';
import type { PropertyListItem, TenantListItem, RentRecordListItem } from '../types/api';
import { formatPaiseToRupees } from '../utils/format';
import { useAuth } from '../auth/AuthContext';

export const PropertiesScreen: React.FC = () => {
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
    <View style={styles.container}>
      <Text style={styles.title}>Properties</Text>
      {loading ? (
        <ActivityIndicator size="small" color="#2563eb" />
      ) : properties.length === 0 ? (
        <Text style={styles.empty}>No properties found.</Text>
      ) : (
        <FlatList
          data={properties}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>{item.name}</Text>
              <Text style={styles.cardSubtitle}>
                {item.unit_count} units ({item.occupied_count} occupied)
              </Text>
            </View>
          )}
        />
      )}
    </View>
  );
};

export const TenantsScreen: React.FC = () => {
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
    <View style={styles.container}>
      <Text style={styles.title}>Tenants</Text>
      {loading ? (
        <ActivityIndicator size="small" color="#2563eb" />
      ) : tenants.length === 0 ? (
        <Text style={styles.empty}>No tenants added.</Text>
      ) : (
        <FlatList
          data={tenants}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>{item.name}</Text>
              <Text style={styles.cardSubtitle}>
                {item.unit.name} ({item.status})
              </Text>
            </View>
          )}
        />
      )}
    </View>
  );
};

export const RentScreen: React.FC = () => {
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
    <View style={styles.container}>
      <Text style={styles.title}>Monthly Rent Register</Text>
      {loading ? (
        <ActivityIndicator size="small" color="#2563eb" />
      ) : records.length === 0 ? (
        <Text style={styles.empty}>No rent records for this month.</Text>
      ) : (
        <FlatList
          data={records}
          keyExtractor={(item) => item.id}
          renderItem={({ item }) => (
            <View style={styles.card}>
              <Text style={styles.cardTitle}>{item.tenant_name}</Text>
              <Text style={styles.cardSubtitle}>
                {item.unit_name} — {formatPaiseToRupees(item.expected_amount_paise)} [{item.status}]
              </Text>
            </View>
          )}
        />
      )}
    </View>
  );
};

export const PaymentsScreen: React.FC = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Payments</Text>
    <Text style={styles.empty}>Payment recording foundation initialized.</Text>
  </View>
);

export const RemindersScreen: React.FC = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Reminders</Text>
    <Text style={styles.empty}>WhatsApp reminder foundation initialized.</Text>
  </View>
);

export const ReportsScreen: React.FC = () => (
  <View style={styles.container}>
    <Text style={styles.title}>Reports</Text>
    <Text style={styles.empty}>Monthly reports foundation initialized.</Text>
  </View>
);

export const SettingsScreen: React.FC = () => {
  const { user, logout } = useAuth();
  return (
    <View style={styles.container}>
      <Text style={styles.title}>Settings</Text>
      <Text style={styles.label}>Name: {user?.full_name}</Text>
      <Text style={styles.label}>Email: {user?.email}</Text>

      <TouchableOpacity style={styles.logoutBtn} onPress={logout}>
        <Text style={styles.logoutText}>Sign Out</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: '#ffffff',
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0f172a',
    marginBottom: 12,
  },
  empty: {
    color: '#64748b',
    fontSize: 14,
    marginTop: 8,
  },
  card: {
    backgroundColor: '#f8fafc',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  cardTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#1e293b',
  },
  cardSubtitle: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 2,
  },
  label: {
    fontSize: 14,
    color: '#334155',
    marginBottom: 8,
  },
  logoutBtn: {
    backgroundColor: '#dc2626',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 24,
  },
  logoutText: {
    color: '#ffffff',
    fontWeight: 'bold',
    fontSize: 15,
  },
});
