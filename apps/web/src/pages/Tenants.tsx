import React, { useEffect, useState, useCallback } from 'react';
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
  Select,
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

export const TenantsPage: React.FC = () => {
  // Navigation & Selection
  const [activeTab, setActiveTab] = useState<TenantTab>('ACTIVE');
  const [selectedTenantId, setSelectedTenantId] = useState<string | null>(null);

  // Tenant List State
  const [tenants, setTenants] = useState<TenantListItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Tenant Detail State
  const [tenantDetail, setTenantDetail] = useState<TenantDetail | null>(null);
  const [detailLoading, setDetailLoading] = useState<boolean>(false);
  const [detailError, setDetailError] = useState<string | null>(null);

  // Toast State
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

  // Move Out Dialog State
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
    } catch (err: any) {
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

  const handleCreateTenant = async (e: React.FormEvent) => {
    e.preventDefault();
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
      setCreateFormError('Please select a valid move-in date.');
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

  const handleEditTenant = async (e: React.FormEvent) => {
    e.preventDefault();
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
      // Reload tenant details to show INACTIVE status & move-out date
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <Skeleton height={32} width={120} />
          <Skeleton height={140} borderRadius={12} />
          <Skeleton height={200} borderRadius={12} />
        </div>
      );
    }

    if (detailError || !tenantDetail) {
      return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
          <button
            onClick={() => setSelectedTenantId(null)}
            style={{
              background: 'none',
              border: 'none',
              color: '#2563eb',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: 0,
            }}
          >
            ← Back to Tenants
          </button>
          <ErrorState
            message={detailError || 'The requested tenant could not be found.'}
            onRetry={() => setSelectedTenantId(null)}
          />
        </div>
      );
    }

    const isActive = tenantDetail.status === 'ACTIVE';

    return (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {/* Toast Feedback */}
        {toastMessage && (
          <div
            style={{
              backgroundColor: '#0f172a',
              color: '#ffffff',
              padding: '10px 14px',
              borderRadius: 8,
              fontSize: 13,
              fontWeight: 500,
              boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
              display: 'flex',
              alignItems: 'center',
              gap: 8,
            }}
          >
            <span>✓</span> {toastMessage}
          </div>
        )}

        {/* Back Link */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <button
            onClick={() => setSelectedTenantId(null)}
            style={{
              background: 'none',
              border: 'none',
              color: '#2563eb',
              fontSize: 14,
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: 4,
              padding: 0,
            }}
          >
            ← All Tenants
          </button>

          <div style={{ display: 'flex', gap: 8 }}>
            <Button size="sm" variant="outline" onClick={handleOpenEditTenant}>
              Edit Tenant
            </Button>
            {isActive && (
              <Button size="sm" variant="danger" onClick={handleOpenMoveOut}>
                Move Out
              </Button>
            )}
          </div>
        </div>

        {/* Tenant Header & Summary Card */}
        <Card style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', margin: 0 }}>
                  {tenantDetail.name}
                </h1>
                <Badge
                  status={isActive ? 'PAID' : 'VOID'}
                  label={isActive ? 'ACTIVE' : 'FORMER'}
                />
              </div>

              <div style={{ fontSize: 14, fontWeight: 600, color: '#2563eb', marginTop: 4 }}>
                {tenantDetail.unit.property_name} · Unit {tenantDetail.unit.name}
              </div>
            </div>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: 12, marginTop: 16 }}>
            <div style={{ backgroundColor: '#f8fafc', padding: 10, borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>PHONE</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a', marginTop: 2 }}>
                <a
                  href={`tel:${tenantDetail.phone}`}
                  style={{ color: '#0f172a', textDecoration: 'none' }}
                >
                  📞 {tenantDetail.phone}
                </a>
              </div>
            </div>

            <div style={{ backgroundColor: '#f8fafc', padding: 10, borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>MOVE-IN DATE</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a', marginTop: 2 }}>
                📅 {formatIsoDate(tenantDetail.move_in_date)}
              </div>
            </div>

            <div style={{ backgroundColor: '#f8fafc', padding: 10, borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>SECURITY DEPOSIT</div>
              <div style={{ fontSize: 14, fontWeight: 700, color: '#0f172a', marginTop: 2 }}>
                {formatPaiseToRupees(tenantDetail.security_deposit_paise)}
              </div>
            </div>

            <div style={{ backgroundColor: '#f8fafc', padding: 10, borderRadius: 8, border: '1px solid #e2e8f0' }}>
              <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>
                {isActive ? 'STATUS' : 'MOVE-OUT DATE'}
              </div>
              <div style={{ fontSize: 14, fontWeight: 700, color: isActive ? '#16a34a' : '#dc2626', marginTop: 2 }}>
                {isActive ? 'Currently Occupying' : formatIsoDate(tenantDetail.move_out_date)}
              </div>
            </div>
          </div>

          {tenantDetail.email && (
            <div style={{ fontSize: 13, color: '#475569', marginTop: 12 }}>
              ✉️ {tenantDetail.email}
            </div>
          )}

          {tenantDetail.notes && (
            <div style={{ fontSize: 13, color: '#64748b', fontStyle: 'italic', marginTop: 8 }}>
              "{tenantDetail.notes}"
            </div>
          )}
        </Card>

        {/* Rent History Section */}
        <div>
          <h2 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', marginBottom: 10 }}>
            Rent History
          </h2>

          {tenantDetail.rent_history.length === 0 ? (
            <Card style={{ padding: 18, textAlign: 'center', color: '#64748b', fontSize: 14 }}>
              No rent records generated for this tenant yet.
            </Card>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {tenantDetail.rent_history.map((record) => {
                const remainingPaise = Math.max(0, record.expected_amount_paise - record.total_paid_paise);
                return (
                  <Card key={record.id} style={{ padding: 14 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: '#0f172a' }}>
                          {formatMonthYear(record.month, record.year)}
                        </div>
                        <div style={{ fontSize: 13, color: '#64748b', marginTop: 2 }}>
                          Due on {formatIsoDate(record.due_date)}
                        </div>
                        <div style={{ fontSize: 14, fontWeight: 700, color: '#1e293b', marginTop: 4 }}>
                          Expected: {formatPaiseToRupees(record.expected_amount_paise)}
                        </div>
                        {record.status !== 'PAID' && remainingPaise > 0 && (
                          <div style={{ fontSize: 12, fontWeight: 600, color: '#dc2626', marginTop: 2 }}>
                            Remaining: {formatPaiseToRupees(remainingPaise)}
                          </div>
                        )}
                      </div>

                      <Badge status={record.status} />
                    </div>

                    {/* Payments detail if any */}
                    {record.payments && record.payments.length > 0 && (
                      <div
                        style={{
                          marginTop: 10,
                          paddingTop: 8,
                          borderTop: '1px dashed #e2e8f0',
                          fontSize: 12,
                          color: '#475569',
                        }}
                      >
                        <div style={{ fontWeight: 600, marginBottom: 4 }}>Recorded Payments:</div>
                        {record.payments.map((p: any, idx: number) => (
                          <div
                            key={p.id || idx}
                            style={{ display: 'flex', justifyContent: 'space-between', padding: '2px 0' }}
                          >
                            <span>
                              {formatIsoDate(p.paid_date)} · {p.payment_method}
                            </span>
                            <span style={{ fontWeight: 600, color: '#16a34a' }}>
                              +{formatPaiseToRupees(p.amount_paise)}
                            </span>
                          </div>
                        ))}
                      </div>
                    )}
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Edit Tenant Modal */}
        <Modal
          isOpen={isEditOpen}
          onClose={() => setIsEditOpen(false)}
          title="Edit Tenant"
        >
          <form onSubmit={handleEditTenant} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <Input
              label="Full Name"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              placeholder="e.g. Rahul Patil"
              required
              disabled={editFormLoading}
            />

            <Input
              label="Phone Number"
              type="tel"
              value={editPhone}
              onChange={(e) => setEditPhone(e.target.value)}
              placeholder="10-digit mobile number"
              required
              disabled={editFormLoading}
            />

            <Input
              label="Email (Optional)"
              type="email"
              value={editEmail}
              onChange={(e) => setEditEmail(e.target.value)}
              placeholder="tenant@example.com"
              disabled={editFormLoading}
            />

            <Input
              label="Move-In Date"
              type="date"
              value={editMoveInDate}
              onChange={(e) => setEditMoveInDate(e.target.value)}
              required
              disabled={editFormLoading}
            />

            <Input
              label="Security Deposit (₹)"
              type="number"
              value={editDepositRupees}
              onChange={(e) => setEditDepositRupees(e.target.value)}
              min="0"
              disabled={editFormLoading}
            />

            <Input
              label="Notes (Optional)"
              value={editNotes}
              onChange={(e) => setEditNotes(e.target.value)}
              placeholder="Emergency contact, agreement details..."
              disabled={editFormLoading}
            />

            {editFormError && (
              <div style={{ color: '#dc2626', fontSize: 13, backgroundColor: '#fef2f2', padding: 8, borderRadius: 6 }}>
                {editFormError}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
              <Button type="button" variant="outline" onClick={() => setIsEditOpen(false)} disabled={editFormLoading}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" loading={editFormLoading}>
                Save Changes
              </Button>
            </div>
          </form>
        </Modal>

        {/* Move Out Confirmation Dialog */}
        <Modal
          isOpen={isMoveOutOpen}
          onClose={() => setIsMoveOutOpen(false)}
          title={`Move ${tenantDetail.name} out?`}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
            <p style={{ fontSize: 14, color: '#475569', margin: 0, lineHeight: 1.5 }}>
              The tenant will become <strong>inactive</strong> and Unit{' '}
              <strong>{tenantDetail.unit.name}</strong> will become <strong>vacant</strong> for new tenants.
              All past rent and payment history will be permanently preserved.
            </p>

            <Input
              label="Move-Out Date"
              type="date"
              value={moveOutDate}
              onChange={(e) => setMoveOutDate(e.target.value)}
              disabled={moveOutLoading}
            />

            {moveOutError && (
              <div style={{ color: '#dc2626', fontSize: 13, backgroundColor: '#fef2f2', padding: 8, borderRadius: 6 }}>
                {moveOutError}
              </div>
            )}

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
              <Button
                type="button"
                variant="outline"
                onClick={() => setIsMoveOutOpen(false)}
                disabled={moveOutLoading}
              >
                Cancel
              </Button>
              <Button
                type="button"
                variant="danger"
                loading={moveOutLoading}
                onClick={handleConfirmMoveOut}
              >
                Confirm Move Out
              </Button>
            </div>
          </div>
        </Modal>
      </div>
    );
  }

  // ==========================================
  // Render Tenants List View
  // ==========================================
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Toast Feedback */}
      {toastMessage && (
        <div
          style={{
            backgroundColor: '#0f172a',
            color: '#ffffff',
            padding: '10px 14px',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 500,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
            display: 'flex',
            alignItems: 'center',
            gap: 8,
          }}
        >
          <span>✓</span> {toastMessage}
        </div>
      )}

      {/* Screen Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1 style={{ fontSize: 20, fontWeight: 800, color: '#0f172a', margin: 0 }}>
            Tenants
          </h1>
          <p style={{ fontSize: 13, color: '#64748b', margin: '2px 0 0' }}>
            Manage current and former occupants
          </p>
        </div>

        <Button size="sm" variant="primary" onClick={handleOpenCreateTenant}>
          + Add Tenant
        </Button>
      </div>

      {/* Filter Tabs (Active / Former / All) */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          backgroundColor: '#f1f5f9',
          borderRadius: 8,
          padding: 4,
          gap: 4,
        }}
      >
        {(['ACTIVE', 'INACTIVE', 'ALL'] as TenantTab[]).map((tab) => {
          const isSelected = activeTab === tab;
          const label = tab === 'ACTIVE' ? 'Active' : tab === 'INACTIVE' ? 'Former' : 'All';
          return (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                border: 'none',
                backgroundColor: isSelected ? '#ffffff' : 'transparent',
                color: isSelected ? '#2563eb' : '#64748b',
                fontWeight: isSelected ? 700 : 500,
                fontSize: 13,
                padding: '8px 0',
                borderRadius: 6,
                cursor: 'pointer',
                boxShadow: isSelected ? '0 1px 3px rgba(0,0,0,0.08)' : 'none',
                transition: 'all 0.15s ease',
              }}
            >
              {label}
            </button>
          );
        })}
      </div>

      {/* Main List Content */}
      {loading ? (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <Skeleton height={80} borderRadius={10} />
          <Skeleton height={80} borderRadius={10} />
          <Skeleton height={80} borderRadius={10} />
        </div>
      ) : error ? (
        <ErrorState
          message={error}
          onRetry={loadTenants}
        />
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
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {tenants.map((tenant) => {
            const isActive = tenant.status === 'ACTIVE';
            return (
              <Card
                key={tenant.id}
                style={{
                  padding: 14,
                  cursor: 'pointer',
                  border: '1px solid #e2e8f0',
                  transition: 'border-color 0.15s ease',
                }}
                onClick={() => setSelectedTenantId(tenant.id)}
              >
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                      <span style={{ fontWeight: 700, fontSize: 16, color: '#0f172a' }}>
                        {tenant.name}
                      </span>
                      <Badge
                        status={isActive ? 'PAID' : 'VOID'}
                        label={isActive ? 'ACTIVE' : 'FORMER'}
                        size="sm"
                      />
                    </div>

                    <div style={{ fontSize: 14, fontWeight: 600, color: '#2563eb', marginTop: 3 }}>
                      {tenant.unit.property_name} · Unit {tenant.unit.name}
                    </div>

                    <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
                      {isActive ? (
                        <>Moved in {formatIsoDate(tenant.move_in_date)}</>
                      ) : (
                        <>Former Tenant · History preserved</>
                      )}
                    </div>
                  </div>

                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                    {tenant.current_month_rent_status && isActive && (
                      <Badge status={tenant.current_month_rent_status} size="sm" />
                    )}
                    <span style={{ fontSize: 13, color: '#94a3b8' }}>›</span>
                  </div>
                </div>
              </Card>
            );
          })}
        </div>
      )}

      {/* Add Tenant Modal */}
      <Modal
        isOpen={isCreateOpen}
        onClose={() => setIsCreateOpen(false)}
        title="Add Tenant"
      >
        <form onSubmit={handleCreateTenant} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {loadingVacantUnits ? (
            <div style={{ padding: 12, textAlign: 'center', color: '#64748b', fontSize: 13 }}>
              Loading vacant units...
            </div>
          ) : vacantUnits.length === 0 ? (
            <div
              style={{
                backgroundColor: '#fef2f2',
                color: '#b91c1c',
                padding: 12,
                borderRadius: 8,
                fontSize: 13,
                border: '1px solid #fecaca',
              }}
            >
              ⚠️ No vacant units available. All units are currently occupied, or no units exist. Add a unit or move out an existing tenant first.
            </div>
          ) : (
            <Select
              label="Select Vacant Unit"
              value={createUnitId}
              onChange={(e) => setCreateUnitId(e.target.value)}
              options={vacantUnits.map((u) => ({
                value: u.unitId,
                label: `${u.propertyName} — Unit ${u.unitName} (${formatPaiseToRupees(u.monthlyRentPaise)}/mo)`,
              }))}
              required
              disabled={createFormLoading}
            />
          )}

          <Input
            label="Tenant Full Name"
            value={createName}
            onChange={(e) => setCreateName(e.target.value)}
            placeholder="e.g. Rahul Patil"
            required
            disabled={createFormLoading || vacantUnits.length === 0}
          />

          <Input
            label="Phone Number"
            type="tel"
            value={createPhone}
            onChange={(e) => setCreatePhone(e.target.value)}
            placeholder="10-digit mobile (e.g. 9876543210)"
            required
            disabled={createFormLoading || vacantUnits.length === 0}
          />

          <Input
            label="Email Address (Optional)"
            type="email"
            value={createEmail}
            onChange={(e) => setCreateEmail(e.target.value)}
            placeholder="tenant@example.com"
            disabled={createFormLoading || vacantUnits.length === 0}
          />

          <Input
            label="Move-In Date"
            type="date"
            value={createMoveInDate}
            onChange={(e) => setCreateMoveInDate(e.target.value)}
            required
            disabled={createFormLoading || vacantUnits.length === 0}
          />

          <Input
            label="Security Deposit (₹)"
            type="number"
            value={createDepositRupees}
            onChange={(e) => setCreateDepositRupees(e.target.value)}
            placeholder="0"
            min="0"
            disabled={createFormLoading || vacantUnits.length === 0}
          />

          <Input
            label="Notes (Optional)"
            value={createNotes}
            onChange={(e) => setCreateNotes(e.target.value)}
            placeholder="ID proof, permanent address, notes..."
            disabled={createFormLoading || vacantUnits.length === 0}
          />

          {createFormError && (
            <div style={{ color: '#dc2626', fontSize: 13, backgroundColor: '#fef2f2', padding: 8, borderRadius: 6 }}>
              {createFormError}
            </div>
          )}

          <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 8 }}>
            <Button
              type="button"
              variant="outline"
              onClick={() => setIsCreateOpen(false)}
              disabled={createFormLoading}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="primary"
              loading={createFormLoading}
              disabled={vacantUnits.length === 0}
            >
              Assign Tenant
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
