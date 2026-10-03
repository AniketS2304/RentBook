import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Linking,
} from 'react-native';
import { api } from '../api';
import type {
  TenantListItem,
  TenantDetail,
  PropertyListResponse,
} from '../types/api';
import { formatPaiseToRupees, formatIsoDate, formatMonthYear } from '../utils/format';
import {
  Card,
  Badge,
  Button,
  Input,
  Modal,
  Skeleton,
  EmptyState,
  ErrorState,
} from '../components/UI';

export type TenantTab = 'ACTIVE' | 'INACTIVE' | 'ALL';

const INDIAN_PHONE_REGEX = /^(\+91[\-\s]?)?[6789]\d{9}$/;

const getTodayIsoDate = (): string => {
  const today = new Date();
  const y = today.getFullYear();
  const m = String(today.getMonth() + 1).padStart(2, '0');
  const d = String(today.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
};

interface VacantUnitOption {
  unitId: string;
  unitName: string;
  propertyName: string;
  monthlyRentPaise: number;
}

export const TenantsScreen: React.FC = () => {
  // Navigation / Selection
  const [activeTab, setActiveTab] = useState<TenantTab>('ACTIVE');
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);

  // List State
  const [tenants, setTenants] = useState<TenantListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Detail State
  const [tenantDetail, setTenantDetail] = useState<TenantDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Toast / Feedback State
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Add Tenant Modal State
  const [isCreateOpen, setIsCreateOpen] = useState<boolean>(false);
  const [createUnitId, setCreateUnitId] = useState<string>('');
  const [createName, setCreateName] = useState<string>('');
  const [createPhone, setCreatePhone] = useState<string>('');
  const [createEmail, setCreateEmail] = useState<string>('');
  const [createMoveInDate, setCreateMoveInDate] = useState<string>(getTodayIsoDate());
  const [createDepositRupees, setCreateDepositRupees] = useState<string>('0');
  const [createNotes, setCreateNotes] = useState<string>('');
  const [createFormError, setCreateFormError] = useState<string | null>(null);
  const [createFormLoading, setCreateFormLoading] = useState<boolean>(false);
  const [vacantUnits, setVacantUnits] = useState<VacantUnitOption[]>([]);
  const [loadingVacantUnits, setLoadingVacantUnits] = useState<boolean>(false);

  // Edit Tenant Modal State
  const [isEditOpen, setIsEditOpen] = useState<boolean>(false);
  const [editName, setEditName] = useState<string>('');
  const [editPhone, setEditPhone] = useState<string>('');
  const [editEmail, setEditEmail] = useState<string>('');
  const [editMoveInDate, setEditMoveInDate] = useState<string>('');
  const [editDepositRupees, setEditDepositRupees] = useState<string>('0');
  const [editNotes, setEditNotes] = useState<string>('');
  const [editFormError, setEditFormError] = useState<string | null>(null);
  const [editFormLoading, setEditFormLoading] = useState<boolean>(false);

  // Move Out Modal State
  const [isMoveOutOpen, setIsMoveOutOpen] = useState<boolean>(false);
  const [moveOutDate, setMoveOutDate] = useState<string>(getTodayIsoDate());
  const [moveOutLoading, setMoveOutLoading] = useState<boolean>(false);
  const [moveOutError, setMoveOutError] = useState<string | null>(null);

  // ==========================================
  // Data Fetching
  // ==========================================
  const loadTenants = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (activeTab === 'ALL') {
        const [activeRes, inactiveRes] = await Promise.all([
          api.tenants.list({ status: 'ACTIVE', per_page: 100 }),
          api.tenants.list({ status: 'INACTIVE', per_page: 100 }),
        ]);
        setTenants([...(activeRes.items || []), ...(inactiveRes.items || [])]);
      } else {
        const res = await api.tenants.list({ status: activeTab, per_page: 100 });
        setTenants(res.items || []);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to load tenants.');
    } finally {
      setLoading(false);
    }
  }, [activeTab]);

  const loadTenantDetail = useCallback(async (tenantId: string) => {
    setDetailLoading(true);
    setDetailError(null);
    try {
      const data = await api.tenants.get(tenantId);
      setTenantDetail(data);
    } catch (err: any) {
      if (err.status === 404) {
        setDetailError('Tenant not found or has been removed.');
      } else {
        setDetailError(err.message || 'Failed to load tenant details.');
      }
    } finally {
      setDetailLoading(false);
    }
  }, []);

  const loadVacantUnits = useCallback(async () => {
    setLoadingVacantUnits(true);
    try {
      const propRes: PropertyListResponse = await api.properties.list({ include_archived: false, per_page: 100 });
      const options: VacantUnitOption[] = [];

      for (const prop of propRes.items || []) {
        try {
          const detail = await api.properties.get(prop.id);
          for (const u of detail.units || []) {
            if (!u.is_occupied && !u.archived_at) {
              options.push({
                unitId: u.id,
                unitName: u.name,
                propertyName: prop.name,
                monthlyRentPaise: u.monthly_rent_paise,
              });
            }
          }
        } catch {
          // ignore single property detail failure
        }
      }
      setVacantUnits(options);
      if (options.length > 0 && !createUnitId) {
        setCreateUnitId(options[0].unitId);
      }
    } catch {
      // vacant units load error
    } finally {
      setLoadingVacantUnits(false);
    }
  }, [createUnitId]);

  useEffect(() => {
    if (selectedTenantId) {
      loadTenantDetail(selectedTenantId);
    } else {
      loadTenants();
    }
  }, [selectedTenantId, activeTab, loadTenants, loadTenantDetail]);

  // ==========================================
  // Add Tenant Flow
  // ==========================================
  const handleOpenCreateTenant = () => {
    setCreateName('');
    setCreatePhone('');
    setCreateEmail('');
    setCreateMoveInDate(getTodayIsoDate());
    setCreateDepositRupees('0');
    setCreateNotes('');
    setCreateFormError(null);
    setIsCreateOpen(true);
    loadVacantUnits();
  };

  const handleCreateTenant = async () => {
    const nameTrimmed = createName.trim();
    if (!nameTrimmed || nameTrimmed.length < 2) {
      setCreateFormError('Tenant name must be at least 2 characters.');
      return;
    }
    if (nameTrimmed.length > 100) {
      setCreateFormError('Tenant name must be at most 100 characters.');
      return;
    }

    const phoneTrimmed = createPhone.trim();
    if (!INDIAN_PHONE_REGEX.test(phoneTrimmed)) {
      setCreateFormError('Please enter a valid 10-digit Indian mobile number (e.g. 9876543210).');
      return;
    }

    if (!createUnitId) {
      setCreateFormError('Please select a vacant unit.');
      return;
    }

    if (!createMoveInDate) {
      setCreateFormError('Please enter a valid move-in date.');
      return;
    }

    const depositNum = parseFloat(createDepositRupees);
    if (isNaN(depositNum) || depositNum < 0) {
      setCreateFormError('Security deposit must be a valid non-negative amount.');
      return;
    }

    setCreateFormLoading(true);
    setCreateFormError(null);
    try {
      const created = await api.tenants.create({
        unit_id: createUnitId,
        name: nameTrimmed,
        phone: phoneTrimmed,
        email: createEmail.trim() || undefined,
        move_in_date: createMoveInDate,
        security_deposit_paise: Math.round(depositNum * 100),
        notes: createNotes.trim() || undefined,
      });

      setIsCreateOpen(false);
      showToast(`Tenant "${created.name}" assigned successfully!`);
      setSelectedTenantId(created.id);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'UNIT_OCCUPIED') {
        setCreateFormError('This unit already has an active tenant. Refreshing vacant units...');
        loadVacantUnits();
      } else if (err.status === 400 && err.code === 'UNIT_ARCHIVED') {
        setCreateFormError('Cannot assign tenant to an archived unit.');
        loadVacantUnits();
      } else {
        setCreateFormError(err.message || 'Failed to create tenant.');
      }
    } finally {
      setCreateFormLoading(false);
    }
  };

  // ==========================================
  // Edit Tenant Flow
  // ==========================================
  const handleOpenEditTenant = () => {
    if (!tenantDetail) return;
    setEditName(tenantDetail.name);
    setEditPhone(tenantDetail.phone);
    setEditEmail(tenantDetail.email || '');
    setEditMoveInDate(tenantDetail.move_in_date);
    setEditDepositRupees(String(tenantDetail.security_deposit_paise / 100));
    setEditNotes(tenantDetail.notes || '');
    setEditFormError(null);
    setIsEditOpen(true);
  };

  const handleEditTenant = async () => {
    if (!tenantDetail) return;

    const nameTrimmed = editName.trim();
    if (!nameTrimmed || nameTrimmed.length < 2) {
      setEditFormError('Tenant name must be at least 2 characters.');
      return;
    }
    if (nameTrimmed.length > 100) {
      setEditFormError('Tenant name must be at most 100 characters.');
      return;
    }

    const phoneTrimmed = editPhone.trim();
    if (!INDIAN_PHONE_REGEX.test(phoneTrimmed)) {
      setEditFormError('Please enter a valid 10-digit Indian mobile number.');
      return;
    }

    const depositNum = parseFloat(editDepositRupees);
    if (isNaN(depositNum) || depositNum < 0) {
      setEditFormError('Security deposit must be a valid non-negative amount.');
      return;
    }

    setEditFormLoading(true);
    setEditFormError(null);
    try {
      const updated = await api.tenants.update(tenantDetail.id, {
        name: nameTrimmed,
        phone: phoneTrimmed,
        email: editEmail.trim() || null,
        move_in_date: editMoveInDate || null,
        security_deposit_paise: Math.round(depositNum * 100),
        notes: editNotes.trim() || null,
      });

      setTenantDetail(updated);
      setIsEditOpen(false);
      showToast('Tenant updated successfully.');
    } catch (err: any) {
      setEditFormError(err.message || 'Failed to update tenant.');
    } finally {
      setEditFormLoading(false);
    }
  };

  // ==========================================
  // Move Out / Deactivate Flow
  // ==========================================
  const handleOpenMoveOut = () => {
    setMoveOutDate(getTodayIsoDate());
    setMoveOutError(null);
    setIsMoveOutOpen(true);
  };

  const handleConfirmMoveOut = async () => {
    if (!tenantDetail) return;
    setMoveOutLoading(true);
    setMoveOutError(null);
    try {
      await api.tenants.deactivate(tenantDetail.id, {
        move_out_date: moveOutDate || undefined,
      });
      setIsMoveOutOpen(false);
      showToast(`Tenant "${tenantDetail.name}" moved out. Unit is now vacant.`);
      loadTenantDetail(tenantDetail.id);
    } catch (err: any) {
      setMoveOutError(err.message || 'Failed to move out tenant.');
    } finally {
      setMoveOutLoading(false);
    }
  };

  // ==========================================
  // Render Detail View
  // ==========================================
  if (selectedTenantId) {
    if (detailLoading) {
      return (
        <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, gap: 14 }}>
          <Skeleton height={32} width={120} />
          <Skeleton height={140} borderRadius={12} />
          <Skeleton height={200} borderRadius={12} />
        </ScrollView>
      );
    }

    if (detailError || !tenantDetail) {
      return (
        <View style={[styles.container, { padding: 16, gap: 16 }]}>
          <TouchableOpacity onPress={() => setSelectedTenantId(null)} style={styles.backBtn}>
            <Text style={styles.backBtnText}>← Back to Tenants</Text>
          </TouchableOpacity>
          <ErrorState
            message={detailError || 'The requested tenant could not be found.'}
            onRetry={() => setSelectedTenantId(null)}
          />
        </View>
      );
    }

    const isActive = tenantDetail.status === 'ACTIVE';

    return (
      <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, gap: 14 }}>
        {/* Toast Feedback */}
        {toastMessage && (
          <View style={styles.toast}>
            <Text style={styles.toastText}>✓ {toastMessage}</Text>
          </View>
        )}

        {/* Back and Action Bar */}
        <View style={styles.detailActionBar}>
          <TouchableOpacity onPress={() => setSelectedTenantId(null)} style={styles.backBtn}>
            <Text style={styles.backBtnText}>← All Tenants</Text>
          </TouchableOpacity>

          <View style={{ flexDirection: 'row', gap: 8 }}>
            <Button
              title="Edit"
              size="sm"
              variant="outline"
              onPress={handleOpenEditTenant}
            />
            {isActive && (
              <Button
                title="Move Out"
                size="sm"
                variant="danger"
                onPress={handleOpenMoveOut}
              />
            )}
          </View>
        </View>

        {/* Tenant Summary Card */}
        <Card style={{ padding: 16 }}>
          <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <View style={{ flex: 1 }}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 8 }}>
                <Text style={styles.tenantDetailName}>{tenantDetail.name}</Text>
                <Badge
                  status={isActive ? 'PAID' : 'VOID'}
                  label={isActive ? 'ACTIVE' : 'FORMER'}
                />
              </View>

              <Text style={styles.tenantDetailUnit}>
                {tenantDetail.unit.property_name} · Unit {tenantDetail.unit.name}
              </Text>
            </View>
          </View>

          <View style={styles.metaGrid}>
            <TouchableOpacity
              style={styles.metaBox}
              onPress={() => Linking.openURL(`tel:${tenantDetail.phone}`)}
            >
              <Text style={styles.metaLabel}>PHONE</Text>
              <Text style={styles.metaValueBlue}>📞 {tenantDetail.phone}</Text>
            </TouchableOpacity>

            <View style={styles.metaBox}>
              <Text style={styles.metaLabel}>MOVE-IN DATE</Text>
              <Text style={styles.metaValue}>📅 {formatIsoDate(tenantDetail.move_in_date)}</Text>
            </View>

            <View style={styles.metaBox}>
              <Text style={styles.metaLabel}>SECURITY DEPOSIT</Text>
              <Text style={styles.metaValue}>
                {formatPaiseToRupees(tenantDetail.security_deposit_paise)}
              </Text>
            </View>

            <View style={styles.metaBox}>
              <Text style={styles.metaLabel}>
                {isActive ? 'STATUS' : 'MOVE-OUT DATE'}
              </Text>
              <Text style={[styles.metaValue, { color: isActive ? '#16a34a' : '#dc2626' }]}>
                {isActive ? 'Active Tenant' : formatIsoDate(tenantDetail.move_out_date)}
              </Text>
            </View>
          </View>

          {tenantDetail.email ? (
            <Text style={styles.tenantEmailText}>✉️ {tenantDetail.email}</Text>
          ) : null}

          {tenantDetail.notes ? (
            <Text style={styles.tenantNotesText}>"{tenantDetail.notes}"</Text>
          ) : null}
        </Card>

        {/* Rent History Section */}
        <View style={{ gap: 8, marginTop: 4 }}>
          <Text style={styles.sectionTitle}>Rent History</Text>

          {tenantDetail.rent_history.length === 0 ? (
            <Card style={{ padding: 18, alignItems: 'center' }}>
              <Text style={{ color: '#64748b', fontSize: 14 }}>
                No rent records generated for this tenant yet.
              </Text>
            </Card>
          ) : (
            tenantDetail.rent_history.map((record) => {
              const remainingPaise = Math.max(0, record.expected_amount_paise - record.total_paid_paise);
              return (
                <Card key={record.id} style={{ padding: 14 }}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <View style={{ flex: 1 }}>
                      <Text style={styles.rentMonthText}>
                        {formatMonthYear(record.month, record.year)}
                      </Text>
                      <Text style={styles.rentDueText}>
                        Due on {formatIsoDate(record.due_date)}
                      </Text>
                      <Text style={styles.rentAmountText}>
                        Expected: {formatPaiseToRupees(record.expected_amount_paise)}
                      </Text>
                      {record.status !== 'PAID' && remainingPaise > 0 && (
                        <Text style={styles.rentRemainingText}>
                          Remaining: {formatPaiseToRupees(remainingPaise)}
                        </Text>
                      )}
                    </View>

                    <Badge status={record.status} />
                  </View>

                  {record.payments && record.payments.length > 0 && (
                    <View style={styles.paymentsList}>
                      <Text style={styles.paymentsHeader}>Recorded Payments:</Text>
                      {record.payments.map((p: any, idx: number) => (
                        <View key={p.id || idx} style={styles.paymentRow}>
                          <Text style={styles.paymentMethodText}>
                            {formatIsoDate(p.paid_date)} · {p.payment_method}
                          </Text>
                          <Text style={styles.paymentAmountText}>
                            +{formatPaiseToRupees(p.amount_paise)}
                          </Text>
                        </View>
                      ))}
                    </View>
                  )}
                </Card>
              );
            })
          )}
        </View>

        {/* Edit Tenant Modal */}
        <Modal
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          title="Edit Tenant"
        >
          <View style={{ gap: 12 }}>
            <Input
              label="Full Name"
              value={editName}
              onChangeText={setEditName}
              placeholder="e.g. Rahul Patil"
              editable={!editFormLoading}
            />

            <Input
              label="Phone Number"
              value={editPhone}
              onChangeText={setEditPhone}
              placeholder="10-digit mobile number"
              keyboardType="phone-pad"
              editable={!editFormLoading}
            />

            <Input
              label="Email (Optional)"
              value={editEmail}
              onChangeText={setEditEmail}
              placeholder="tenant@example.com"
              keyboardType="email-address"
              editable={!editFormLoading}
            />

            <Input
              label="Move-In Date (YYYY-MM-DD)"
              value={editMoveInDate}
              onChangeText={setEditMoveInDate}
              placeholder="YYYY-MM-DD"
              editable={!editFormLoading}
            />

            <Input
              label="Security Deposit (₹)"
              value={editDepositRupees}
              onChangeText={setEditDepositRupees}
              keyboardType="numeric"
              editable={!editFormLoading}
            />

            <Input
              label="Notes (Optional)"
              value={editNotes}
              onChangeText={setEditNotes}
              placeholder="Emergency contact, agreement details..."
              editable={!editFormLoading}
            />

            {editFormError && (
              <View style={styles.errorBanner}>
                <Text style={styles.errorBannerText}>{editFormError}</Text>
              </View>
            )}

            <View style={styles.modalBtnRow}>
              <Button
                title="Cancel"
                variant="outline"
                onPress={() => setIsEditOpen(false)}
                disabled={editFormLoading}
                style={{ flex: 1 }}
              />
              <Button
                title="Save Changes"
                variant="primary"
                onPress={handleEditTenant}
                loading={editFormLoading}
                style={{ flex: 1 }}
              />
            </View>
          </View>
        </Modal>

        {/* Move Out Confirmation Modal */}
        <Modal
          isOpen={isMoveOutOpen}
          onClose={() => setIsMoveOutOpen(false)}
          title={`Move ${tenantDetail.name} out?`}
        >
          <View style={{ gap: 12 }}>
            <Text style={styles.moveOutWarningText}>
              The tenant will become <Text style={{ fontWeight: 'bold' }}>inactive</Text> and Unit{' '}
              <Text style={{ fontWeight: 'bold' }}>{tenantDetail.unit.name}</Text> will become{' '}
              <Text style={{ fontWeight: 'bold' }}>vacant</Text> for new tenancies.
              Historical rent and payment records are permanently preserved.
            </Text>

            <Input
              label="Move-Out Date (YYYY-MM-DD)"
              value={moveOutDate}
              onChangeText={setMoveOutDate}
              placeholder="YYYY-MM-DD"
              editable={!moveOutLoading}
            />

            {moveOutError && (
              <View style={styles.errorBanner}>
                <Text style={styles.errorBannerText}>{moveOutError}</Text>
              </View>
            )}

            <View style={styles.modalBtnRow}>
              <Button
                title="Cancel"
                variant="outline"
                onPress={() => setIsMoveOutOpen(false)}
                disabled={moveOutLoading}
                style={{ flex: 1 }}
              />
              <Button
                title="Confirm Move Out"
                variant="danger"
                onPress={handleConfirmMoveOut}
                loading={moveOutLoading}
                style={{ flex: 1 }}
              />
            </View>
          </View>
        </Modal>
      </ScrollView>
    );
  }

  // ==========================================
  // Render Tenants List View
  // ==========================================
  return (
    <ScrollView style={styles.container} contentContainerStyle={{ padding: 16, gap: 14 }}>
      {/* Toast Feedback */}
      {toastMessage && (
        <View style={styles.toast}>
          <Text style={styles.toastText}>✓ {toastMessage}</Text>
        </View>
      )}

      {/* Screen Header */}
      <View style={styles.headerRow}>
        <View>
          <Text style={styles.screenTitle}>Tenants</Text>
          <Text style={styles.screenSubtitle}>Manage current and former occupants</Text>
        </View>

        <Button
          title="+ Add Tenant"
          size="sm"
          variant="primary"
          onPress={handleOpenCreateTenant}
        />
      </View>

      {/* Filter Tabs (Active / Former / All) */}
      <View style={styles.tabBar}>
        {(['ACTIVE', 'INACTIVE', 'ALL'] as TenantTab[]).map((tab) => {
          const isSelected = activeTab === tab;
          const label = tab === 'ACTIVE' ? 'Active' : tab === 'INACTIVE' ? 'Former' : 'All';
          return (
            <TouchableOpacity
              key={tab}
              onPress={() => setActiveTab(tab)}
              style={[styles.tabItem, isSelected && styles.tabItemActive]}
            >
              <Text style={[styles.tabText, isSelected && styles.tabTextActive]}>
                {label}
              </Text>
            </TouchableOpacity>
          );
        })}
      </View>

      {/* Main Content */}
      {loading ? (
        <View style={{ gap: 10 }}>
          <Skeleton height={75} borderRadius={10} />
          <Skeleton height={75} borderRadius={10} />
          <Skeleton height={75} borderRadius={10} />
        </View>
      ) : error ? (
        <ErrorState message={error} onRetry={loadTenants} />
      ) : tenants.length === 0 ? (
        <EmptyState
          title={activeTab === 'INACTIVE' ? 'No former tenants' : 'No tenants yet'}
          description={
            activeTab === 'INACTIVE'
              ? 'Past tenants who have moved out will appear here with preserved history.'
              : 'Add tenants to your vacant rental units to start tracking monthly rent obligations.'
          }
          actionLabel={activeTab !== 'INACTIVE' ? '+ Add First Tenant' : undefined}
          onAction={activeTab !== 'INACTIVE' ? handleOpenCreateTenant : undefined}
          icon="👥"
        />
      ) : (
        <View style={{ gap: 10 }}>
          {tenants.map((tenant) => {
            const isActive = tenant.status === 'ACTIVE';
            return (
              <TouchableOpacity
                key={tenant.id}
                activeOpacity={0.7}
                onPress={() => setSelectedTenantId(tenant.id)}
              >
                <Card style={{ padding: 14 }}>
                  <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <View style={{ flex: 1 }}>
                      <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                        <Text style={styles.tenantCardName}>{tenant.name}</Text>
                        <Badge
                          status={isActive ? 'PAID' : 'VOID'}
                          label={isActive ? 'ACTIVE' : 'FORMER'}
                        />
                      </View>

                      <Text style={styles.tenantCardUnit}>
                        {tenant.unit.property_name} · Unit {tenant.unit.name}
                      </Text>

                      <Text style={styles.tenantCardMeta}>
                        {isActive
                          ? `Moved in ${formatIsoDate(tenant.move_in_date)}`
                          : 'Former Tenant · History preserved'}
                      </Text>
                    </View>

                    <View style={{ alignItems: 'flex-end', gap: 6 }}>
                      {tenant.current_month_rent_status && isActive && (
                        <Badge status={tenant.current_month_rent_status} />
                      )}
                      <Text style={{ fontSize: 16, color: '#94a3b8' }}>›</Text>
                    </View>
                  </View>
                </Card>
              </TouchableOpacity>
            );
          })}
        </View>
      )}

      {/* Add Tenant Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Tenant"
      >
        <View style={{ gap: 12 }}>
          {loadingVacantUnits ? (
            <Text style={{ textAlign: 'center', color: '#64748b', fontSize: 13, padding: 8 }}>
              Loading vacant units...
            </Text>
          ) : vacantUnits.length === 0 ? (
            <View style={styles.errorBanner}>
              <Text style={styles.errorBannerText}>
                ⚠️ No vacant units available. All units are occupied, or no units exist. Add a unit or move out an existing tenant first.
              </Text>
            </View>
          ) : (
            <View>
              <Text style={styles.inputLabel}>SELECT VACANT UNIT *</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginVertical: 6 }}>
                <View style={{ flexDirection: 'row', gap: 8 }}>
                  {vacantUnits.map((u) => {
                    const isSelected = createUnitId === u.unitId;
                    return (
                      <TouchableOpacity
                        key={u.unitId}
                        onPress={() => setCreateUnitId(u.unitId)}
                        style={[
                          styles.unitChip,
                          isSelected && styles.unitChipSelected,
                        ]}
                      >
                        <Text style={[styles.unitChipTitle, isSelected && styles.unitChipTextSelected]}>
                          {u.propertyName} · {u.unitName}
                        </Text>
                        <Text style={[styles.unitChipSub, isSelected && styles.unitChipTextSelected]}>
                          {formatPaiseToRupees(u.monthlyRentPaise)}/mo
                        </Text>
                      </TouchableOpacity>
                    );
                  })}
                </View>
              </ScrollView>
            </View>
          )}

          <Input
            label="Tenant Full Name *"
            value={createName}
            onChangeText={setCreateName}
            placeholder="e.g. Rahul Patil"
            editable={!createFormLoading && vacantUnits.length > 0}
          />

          <Input
            label="Phone Number *"
            value={createPhone}
            onChangeText={setCreatePhone}
            placeholder="10-digit mobile number"
            keyboardType="phone-pad"
            editable={!createFormLoading && vacantUnits.length > 0}
          />

          <Input
            label="Email Address (Optional)"
            value={createEmail}
            onChangeText={setCreateEmail}
            placeholder="tenant@example.com"
            keyboardType="email-address"
            editable={!createFormLoading && vacantUnits.length > 0}
          />

          <Input
            label="Move-In Date (YYYY-MM-DD) *"
            value={createMoveInDate}
            onChangeText={setCreateMoveInDate}
            placeholder="YYYY-MM-DD"
            editable={!createFormLoading && vacantUnits.length > 0}
          />

          <Input
            label="Security Deposit (₹)"
            value={createDepositRupees}
            onChangeText={setCreateDepositRupees}
            placeholder="0"
            keyboardType="numeric"
            editable={!createFormLoading && vacantUnits.length > 0}
          />

          <Input
            label="Notes (Optional)"
            value={createNotes}
            onChangeText={setCreateNotes}
            placeholder="Identity proof, emergency contact..."
            editable={!createFormLoading && vacantUnits.length > 0}
          />

          {createFormError && (
            <View style={styles.errorBanner}>
              <Text style={styles.errorBannerText}>{createFormError}</Text>
            </View>
          )}

          <View style={styles.modalBtnRow}>
            <Button
              title="Cancel"
              variant="outline"
              onPress={() => setIsCreateOpen(false)}
              disabled={createFormLoading}
              style={{ flex: 1 }}
            />
            <Button
              title="Assign Tenant"
              variant="primary"
              onPress={handleCreateTenant}
              loading={createFormLoading}
              disabled={vacantUnits.length === 0}
              style={{ flex: 1 }}
            />
          </View>
        </View>
      </Modal>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
  },
  toast: {
    backgroundColor: '#0f172a',
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 8,
  },
  toastText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0f172a',
  },
  screenSubtitle: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  tabBar: {
    flexDirection: 'row',
    backgroundColor: '#f1f5f9',
    borderRadius: 8,
    padding: 3,
    gap: 4,
  },
  tabItem: {
    flex: 1,
    paddingVertical: 8,
    alignItems: 'center',
    borderRadius: 6,
  },
  tabItemActive: {
    backgroundColor: '#ffffff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2,
  },
  tabText: {
    fontSize: 13,
    fontWeight: '500',
    color: '#64748b',
  },
  tabTextActive: {
    fontWeight: '700',
    color: '#2563eb',
  },
  tenantCardName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0f172a',
  },
  tenantCardUnit: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2563eb',
    marginTop: 2,
  },
  tenantCardMeta: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 4,
  },
  detailActionBar: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  backBtn: {
    paddingVertical: 4,
    paddingRight: 8,
  },
  backBtnText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2563eb',
  },
  tenantDetailName: {
    fontSize: 20,
    fontWeight: '800',
    color: '#0f172a',
  },
  tenantDetailUnit: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2563eb',
    marginTop: 4,
  },
  metaGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 14,
  },
  metaBox: {
    width: '48%',
    backgroundColor: '#f8fafc',
    padding: 10,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  metaLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: '#64748b',
  },
  metaValue: {
    fontSize: 13,
    fontWeight: '700',
    color: '#0f172a',
    marginTop: 2,
  },
  metaValueBlue: {
    fontSize: 13,
    fontWeight: '700',
    color: '#2563eb',
    marginTop: 2,
  },
  tenantEmailText: {
    fontSize: 13,
    color: '#475569',
    marginTop: 10,
  },
  tenantNotesText: {
    fontSize: 13,
    color: '#64748b',
    fontStyle: 'italic',
    marginTop: 6,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#0f172a',
  },
  rentMonthText: {
    fontSize: 15,
    fontWeight: '700',
    color: '#0f172a',
  },
  rentDueText: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  rentAmountText: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1e293b',
    marginTop: 4,
  },
  rentRemainingText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#dc2626',
    marginTop: 2,
  },
  paymentsList: {
    marginTop: 8,
    paddingTop: 8,
    borderTopWidth: 1,
    borderTopColor: '#e2e8f0',
    borderStyle: 'dashed',
  },
  paymentsHeader: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
    marginBottom: 4,
  },
  paymentRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 2,
  },
  paymentMethodText: {
    fontSize: 12,
    color: '#475569',
  },
  paymentAmountText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#16a34a',
  },
  modalBtnRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 8,
  },
  errorBanner: {
    backgroundColor: '#fef2f2',
    borderColor: '#fecaca',
    borderWidth: 1,
    padding: 10,
    borderRadius: 8,
  },
  errorBannerText: {
    color: '#dc2626',
    fontSize: 13,
    lineHeight: 18,
  },
  moveOutWarningText: {
    fontSize: 14,
    color: '#475569',
    lineHeight: 20,
  },
  inputLabel: {
    fontSize: 12,
    fontWeight: '700',
    color: '#475569',
    marginBottom: 4,
  },
  unitChip: {
    paddingVertical: 8,
    paddingHorizontal: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#cbd5e1',
    backgroundColor: '#f8fafc',
  },
  unitChipSelected: {
    borderColor: '#2563eb',
    backgroundColor: '#eff6ff',
  },
  unitChipTitle: {
    fontSize: 13,
    fontWeight: '700',
    color: '#1e293b',
  },
  unitChipSub: {
    fontSize: 11,
    color: '#64748b',
    marginTop: 2,
  },
  unitChipTextSelected: {
    color: '#1d4ed8',
  },
});
