import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../api';
import type {
  PropertyListItem,
  PropertyDetail,
  UnitOut,
  UnitType,
} from '../types/api';
import { formatPaiseToRupees } from '../utils/format';
import {
  Card,
  Badge,
  Button,
  Input,
  Select,
  Modal,
  ConfirmDialog,
  Skeleton,
  EmptyState,
  ErrorState,
} from '../components/UI';

const UNIT_TYPE_OPTIONS: Array<{ value: UnitType; label: string }> = [
  { value: 'FLAT', label: 'Flat / Apartment' },
  { value: 'ROOM', label: 'Room' },
  { value: 'SHOP', label: 'Shop / Commercial' },
  { value: 'OTHER', label: 'Other' },
];

export const PropertiesPage: React.FC = () => {
  // Navigation / Active View
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);

  // Data states
  const [properties, setProperties] = useState<PropertyListItem[]>([]);
  const [propertyDetail, setPropertyDetail] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // Property Modals
  const [isCreatePropertyOpen, setIsCreatePropertyOpen] = useState(false);
  const [isEditPropertyOpen, setIsEditPropertyOpen] = useState(false);
  const [isArchivePropertyOpen, setIsArchivePropertyOpen] = useState(false);
  const [propertyFormLoading, setPropertyFormLoading] = useState(false);
  const [propertyFormError, setPropertyFormError] = useState<string | null>(null);
  const [propertyName, setPropertyName] = useState('');
  const [propertyAddress, setPropertyAddress] = useState('');
  const [propertyNotes, setPropertyNotes] = useState('');

  // Unit Modals
  const [isCreateUnitOpen, setIsCreateUnitOpen] = useState(false);
  const [editingUnit, setEditingUnit] = useState<UnitOut | null>(null);
  const [archivingUnit, setArchivingUnit] = useState<UnitOut | null>(null);
  const [unitFormLoading, setUnitFormLoading] = useState(false);
  const [unitFormError, setUnitFormError] = useState<string | null>(null);
  const [unitName, setUnitName] = useState('');
  const [unitType, setUnitType] = useState<UnitType>('FLAT');
  const [unitRentRupees, setUnitRentRupees] = useState('');
  const [unitDueDay, setUnitDueDay] = useState('5');
  const [unitNotes, setUnitNotes] = useState('');

  // Assign Tenant from Vacant Unit
  const [assigningUnit, setAssigningUnit] = useState<UnitOut | null>(null);
  const [tenantName, setTenantName] = useState('');
  const [tenantPhone, setTenantPhone] = useState('');
  const [tenantEmail, setTenantEmail] = useState('');
  const [tenantMoveInDate, setTenantMoveInDate] = useState(() => {
    const today = new Date();
    return `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`;
  });
  const [tenantDepositRupees, setTenantDepositRupees] = useState('0');
  const [tenantNotes, setTenantNotes] = useState('');
  const [tenantFormLoading, setTenantFormLoading] = useState(false);
  const [tenantFormError, setTenantFormError] = useState<string | null>(null);

  const handleOpenAssignTenant = (unit: UnitOut) => {
    setAssigningUnit(unit);
    setTenantName('');
    setTenantPhone('');
    setTenantEmail('');
    const today = new Date();
    setTenantMoveInDate(`${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}-${String(today.getDate()).padStart(2, '0')}`);
    setTenantDepositRupees('0');
    setTenantNotes('');
    setTenantFormError(null);
  };

  const handleCreateTenantForUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!assigningUnit || !propertyDetail) return;
    const nameTrimmed = tenantName.trim();
    if (!nameTrimmed || nameTrimmed.length < 2) {
      setTenantFormError('Tenant name must be at least 2 characters.');
      return;
    }
    const phoneTrimmed = tenantPhone.trim();
    const phoneRegex = /^(\+91[\-\s]?)?[6789]\d{9}$/;
    if (!phoneRegex.test(phoneTrimmed)) {
      setTenantFormError('Please enter a valid 10-digit Indian mobile number (e.g. 9876543210).');
      return;
    }
    const depositNum = parseFloat(tenantDepositRupees);
    if (isNaN(depositNum) || depositNum < 0) {
      setTenantFormError('Security deposit must be a valid non-negative amount.');
      return;
    }

    setTenantFormLoading(true);
    setTenantFormError(null);
    try {
      await api.tenants.create({
        unit_id: assigningUnit.id,
        name: nameTrimmed,
        phone: phoneTrimmed,
        email: tenantEmail.trim() || undefined,
        move_in_date: tenantMoveInDate,
        security_deposit_paise: Math.round(depositNum * 100),
        notes: tenantNotes.trim() || undefined,
      });
      setAssigningUnit(null);
      showToast(`Tenant "${nameTrimmed}" assigned to Unit ${assigningUnit.name}!`);
      loadPropertyDetail(propertyDetail.id);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'UNIT_OCCUPIED') {
        setTenantFormError('This unit already has an active tenant. Refreshing...');
        loadPropertyDetail(propertyDetail.id);
      } else {
        setTenantFormError(err.message || 'Failed to add tenant.');
      }
    } finally {
      setTenantFormLoading(false);
    }
  };

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3500);
  };

  // Fetch properties list
  const loadProperties = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.properties.list({ per_page: 100 });
      setProperties(res.items);
    } catch (err: any) {
      setError(err.message || 'Failed to load properties.');
    } finally {
      setLoading(false);
    }
  }, []);

  // Fetch property detail
  const loadPropertyDetail = useCallback(async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.properties.get(id);
      setPropertyDetail(res);
    } catch (err: any) {
      if (err.status === 404) {
        setError('Property not found or you do not have permission to view it.');
      } else {
        setError(err.message || 'Failed to load property details.');
      }
      setPropertyDetail(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedPropertyId) {
      loadPropertyDetail(selectedPropertyId);
    } else {
      loadProperties();
    }
  }, [selectedPropertyId, loadProperties, loadPropertyDetail]);

  // ==========================================
  // Property Actions
  // ==========================================
  const handleOpenCreateProperty = () => {
    setPropertyName('');
    setPropertyAddress('');
    setPropertyNotes('');
    setPropertyFormError(null);
    setIsCreatePropertyOpen(true);
  };

  const handleCreateProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = propertyName.trim();
    if (!trimmed) {
      setPropertyFormError('Property name is required.');
      return;
    }
    setPropertyFormLoading(true);
    setPropertyFormError(null);
    try {
      const created = await api.properties.create({
        name: trimmed,
        address: propertyAddress.trim() || undefined,
        notes: propertyNotes.trim() || undefined,
      });
      setIsCreatePropertyOpen(false);
      showToast(`Property "${created.name}" created successfully`);
      setSelectedPropertyId(created.id);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'PROPERTY_NAME_CONFLICT') {
        setPropertyFormError('A property with this name already exists.');
      } else {
        setPropertyFormError(err.message || 'Failed to create property.');
      }
    } finally {
      setPropertyFormLoading(false);
    }
  };

  const handleOpenEditProperty = () => {
    if (!propertyDetail) return;
    setPropertyName(propertyDetail.name);
    setPropertyAddress(propertyDetail.address || '');
    setPropertyNotes(propertyDetail.notes || '');
    setPropertyFormError(null);
    setIsEditPropertyOpen(true);
  };

  const handleEditProperty = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!propertyDetail) return;
    const trimmed = propertyName.trim();
    if (!trimmed) {
      setPropertyFormError('Property name is required.');
      return;
    }
    setPropertyFormLoading(true);
    setPropertyFormError(null);
    try {
      const updated = await api.properties.update(propertyDetail.id, {
        name: trimmed,
        address: propertyAddress.trim() || null,
        notes: propertyNotes.trim() || null,
      });
      setPropertyDetail(updated);
      setIsEditPropertyOpen(false);
      showToast('Property updated successfully');
    } catch (err: any) {
      if (err.status === 409 || err.code === 'PROPERTY_NAME_CONFLICT') {
        setPropertyFormError('A property with this name already exists.');
      } else {
        setPropertyFormError(err.message || 'Failed to update property.');
      }
    } finally {
      setPropertyFormLoading(false);
    }
  };

  const handleArchiveProperty = async () => {
    if (!propertyDetail) return;
    setPropertyFormLoading(true);
    try {
      await api.properties.archive(propertyDetail.id);
      setIsArchivePropertyOpen(false);
      showToast(`Property "${propertyDetail.name}" archived`);
      setSelectedPropertyId(null);
    } catch (err: any) {
      showToast(err.message || 'Failed to archive property.');
    } finally {
      setPropertyFormLoading(false);
    }
  };

  // ==========================================
  // Unit Actions
  // ==========================================
  const handleOpenCreateUnit = () => {
    setUnitName('');
    setUnitType('FLAT');
    setUnitRentRupees('');
    setUnitDueDay('5');
    setUnitNotes('');
    setUnitFormError(null);
    setIsCreateUnitOpen(true);
  };

  const handleCreateUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!propertyDetail) return;
    const trimmed = unitName.trim();
    if (!trimmed) {
      setUnitFormError('Unit name or number is required.');
      return;
    }
    const rentNum = parseFloat(unitRentRupees);
    if (isNaN(rentNum) || rentNum <= 0) {
      setUnitFormError('Please enter a valid monthly rent greater than 0.');
      return;
    }
    const dueDayNum = parseInt(unitDueDay, 10);
    if (isNaN(dueDayNum) || dueDayNum < 1 || dueDayNum > 28) {
      setUnitFormError('Due day must be between 1 and 28.');
      return;
    }

    setUnitFormLoading(true);
    setUnitFormError(null);
    try {
      await api.units.create(propertyDetail.id, {
        name: trimmed,
        unit_type: unitType,
        monthly_rent_paise: Math.round(rentNum * 100),
        rent_due_day: dueDayNum,
        notes: unitNotes.trim() || undefined,
      });
      setIsCreateUnitOpen(false);
      showToast(`Unit "${trimmed}" added successfully`);
      loadPropertyDetail(propertyDetail.id);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'UNIT_NAME_CONFLICT') {
        setUnitFormError('A unit with this name already exists in this property.');
      } else {
        setUnitFormError(err.message || 'Failed to create unit.');
      }
    } finally {
      setUnitFormLoading(false);
    }
  };

  const handleOpenEditUnit = (unit: UnitOut) => {
    setEditingUnit(unit);
    setUnitName(unit.name);
    setUnitType((unit.unit_type as UnitType) || 'FLAT');
    setUnitRentRupees(String(unit.monthly_rent_paise / 100));
    setUnitDueDay(String(unit.rent_due_day));
    setUnitNotes(unit.notes || '');
    setUnitFormError(null);
  };

  const handleEditUnit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!editingUnit || !propertyDetail) return;
    const trimmed = unitName.trim();
    if (!trimmed) {
      setUnitFormError('Unit name or number is required.');
      return;
    }
    const rentNum = parseFloat(unitRentRupees);
    if (isNaN(rentNum) || rentNum <= 0) {
      setUnitFormError('Please enter a valid monthly rent greater than 0.');
      return;
    }
    const dueDayNum = parseInt(unitDueDay, 10);
    if (isNaN(dueDayNum) || dueDayNum < 1 || dueDayNum > 28) {
      setUnitFormError('Due day must be between 1 and 28.');
      return;
    }

    setUnitFormLoading(true);
    setUnitFormError(null);
    try {
      await api.units.update(editingUnit.id, {
        name: trimmed,
        unit_type: unitType,
        monthly_rent_paise: Math.round(rentNum * 100),
        rent_due_day: dueDayNum,
        notes: unitNotes.trim() || null,
      });
      setEditingUnit(null);
      showToast(`Unit "${trimmed}" updated successfully`);
      loadPropertyDetail(propertyDetail.id);
    } catch (err: any) {
      if (err.status === 409 || err.code === 'UNIT_NAME_CONFLICT') {
        setUnitFormError('A unit with this name already exists in this property.');
      } else {
        setUnitFormError(err.message || 'Failed to update unit.');
      }
    } finally {
      setUnitFormLoading(false);
    }
  };

  const handleArchiveUnit = async () => {
    if (!archivingUnit || !propertyDetail) return;
    setUnitFormLoading(true);
    try {
      await api.units.archive(archivingUnit.id);
      showToast(`Unit "${archivingUnit.name}" archived`);
      setArchivingUnit(null);
      loadPropertyDetail(propertyDetail.id);
    } catch (err: any) {
      showToast(err.message || 'Failed to archive unit.');
    } finally {
      setUnitFormLoading(false);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Toast Notification */}
      {toastMessage && (
        <div
          role="status"
          style={{
            position: 'fixed',
            top: 16,
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 150,
            background: '#0f172a',
            color: '#ffffff',
            padding: '10px 18px',
            borderRadius: 8,
            fontSize: 13,
            fontWeight: 500,
            boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
          }}
        >
          {toastMessage}
        </div>
      )}

      {/* ======================================================== */}
      {/* VIEW: PROPERTY DETAIL (when a property is selected)     */}
      {/* ======================================================== */}
      {selectedPropertyId ? (
        <div>
          {/* Back button & Property Header */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <button
              onClick={() => setSelectedPropertyId(null)}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: 6,
                background: 'none',
                border: 'none',
                color: '#2563eb',
                fontSize: 14,
                fontWeight: 600,
                cursor: 'pointer',
                padding: '4px 0',
              }}
            >
              ← All Properties
            </button>
            <div style={{ display: 'flex', gap: 8 }}>
              <Button size="sm" variant="outline" onClick={handleOpenEditProperty}>
                Edit
              </Button>
              <Button size="sm" variant="danger" onClick={() => setIsArchivePropertyOpen(true)}>
                Archive
              </Button>
            </div>
          </div>

          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Skeleton height={32} width="60%" />
              <Skeleton height={20} width="40%" />
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 10 }}>
                <Skeleton height={70} />
                <Skeleton height={70} />
                <Skeleton height={70} />
              </div>
            </div>
          )}

          {error && !loading && (
            <ErrorState
              message={error}
              onRetry={() => loadPropertyDetail(selectedPropertyId)}
            />
          )}

          {!loading && propertyDetail && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
              {/* Property Info Card */}
              <Card>
                <h1 style={{ fontSize: 22, fontWeight: 700, color: '#0f172a', margin: 0 }}>
                  {propertyDetail.name}
                </h1>
                {propertyDetail.address ? (
                  <p style={{ fontSize: 13, color: '#64748b', marginTop: 4, marginBottom: 0 }}>
                    📍 {propertyDetail.address}
                  </p>
                ) : null}
                {propertyDetail.notes ? (
                  <p style={{ fontSize: 12, color: '#64748b', marginTop: 4, fontStyle: 'italic', marginBottom: 0 }}>
                    "{propertyDetail.notes}"
                  </p>
                ) : null}

                {/* Occupancy Counts Row */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, marginTop: 14 }}>
                  <div style={{ backgroundColor: '#f8fafc', padding: 10, borderRadius: 8, textAlign: 'center', border: '1px solid #e2e8f0' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>TOTAL</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: '#0f172a' }}>{propertyDetail.unit_count}</div>
                  </div>
                  <div style={{ backgroundColor: '#f0fdf4', padding: 10, borderRadius: 8, textAlign: 'center', border: '1px solid #bbf7d0' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: '#16a34a' }}>OCCUPIED</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: '#15803d' }}>{propertyDetail.occupied_count}</div>
                  </div>
                  <div style={{ backgroundColor: '#fef2f2', padding: 10, borderRadius: 8, textAlign: 'center', border: '1px solid #fecaca' }}>
                    <div style={{ fontSize: 11, fontWeight: 600, color: '#dc2626' }}>VACANT</div>
                    <div style={{ fontSize: 18, fontWeight: 700, color: '#b91c1c' }}>{propertyDetail.vacant_count}</div>
                  </div>
                </div>
              </Card>

              {/* Units Header + Add Unit Button */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <h2 style={{ fontSize: 16, fontWeight: 700, color: '#0f172a', margin: 0 }}>
                  Units ({propertyDetail.units.length})
                </h2>
                <Button size="sm" variant="primary" onClick={handleOpenCreateUnit}>
                  + Add Unit
                </Button>
              </div>

              {/* Units List */}
              {propertyDetail.units.length === 0 ? (
                <EmptyState
                  title="No units added yet"
                  description="Add units (flats, rooms, shops) to this property to manage tenants and collect rent."
                  actionLabel="+ Add First Unit"
                  onAction={handleOpenCreateUnit}
                  icon="🚪"
                />
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {propertyDetail.units.map((unit) => (
                    <Card key={unit.id} style={{ padding: 14 }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                            <span style={{ fontWeight: 700, fontSize: 16, color: '#0f172a' }}>
                              {unit.name}
                            </span>
                            <Badge status={unit.unit_type} size="sm" />
                          </div>
                          <div style={{ fontSize: 14, fontWeight: 700, color: '#1e293b', marginTop: 4 }}>
                            {formatPaiseToRupees(unit.monthly_rent_paise)}{' '}
                            <span style={{ fontSize: 12, fontWeight: 400, color: '#64748b' }}>
                              / month · Due on {unit.rent_due_day}th
                            </span>
                          </div>
                          {unit.notes ? (
                            <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>
                              {unit.notes}
                            </div>
                          ) : null}
                        </div>

                        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: 6 }}>
                          <Badge
                            status={unit.is_occupied ? 'OCCUPIED' : 'VACANT'}
                            label={
                              unit.is_occupied
                                ? unit.current_tenant
                                  ? `Occupied · ${unit.current_tenant.name}`
                                  : 'Occupied'
                                : 'Vacant'
                            }
                          />
                          <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
                            {!unit.is_occupied && (
                              <>
                                <button
                                  onClick={() => handleOpenAssignTenant(unit)}
                                  style={{
                                    background: 'none',
                                    border: 'none',
                                    color: '#16a34a',
                                    fontSize: 12,
                                    fontWeight: 600,
                                    cursor: 'pointer',
                                  }}
                                >
                                  + Add Tenant
                                </button>
                                <span style={{ color: '#cbd5e1' }}>·</span>
                              </>
                            )}
                            <button
                              onClick={() => handleOpenEditUnit(unit)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#2563eb',
                                fontSize: 12,
                                fontWeight: 600,
                                cursor: 'pointer',
                              }}
                            >
                              Edit
                            </button>
                            <span style={{ color: '#cbd5e1' }}>·</span>
                            <button
                              onClick={() => setArchivingUnit(unit)}
                              style={{
                                background: 'none',
                                border: 'none',
                                color: '#dc2626',
                                fontSize: 12,
                                fontWeight: 600,
                                cursor: 'pointer',
                              }}
                            >
                              Archive
                            </button>
                          </div>
                        </div>
                      </div>
                    </Card>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      ) : (
        /* ======================================================== */
        /* VIEW: PROPERTIES LIST                                    */
        /* ======================================================== */
        <div>
          {/* Header & Add Button */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
            <div>
              <h1 style={{ fontSize: 20, fontWeight: 700, color: '#0f172a', margin: 0 }}>
                Properties
              </h1>
              <p style={{ fontSize: 13, color: '#64748b', margin: '2px 0 0 0' }}>
                Manage buildings and complexes
              </p>
            </div>
            <Button size="sm" variant="primary" onClick={handleOpenCreateProperty}>
              + Add Property
            </Button>
          </div>

          {loading && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
              <Skeleton height={80} />
              <Skeleton height={80} />
              <Skeleton height={80} />
            </div>
          )}

          {error && !loading && (
            <ErrorState message={error} onRetry={loadProperties} />
          )}

          {!loading && !error && properties.length === 0 && (
            <EmptyState
              title="No properties yet"
              description="Add your first property to start tracking rental units, tenant occupancy, and monthly rent."
              actionLabel="+ Add Property"
              onAction={handleOpenCreateProperty}
              icon="🏢"
            />
          )}

          {!loading && !error && properties.length > 0 && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {properties.map((prop) => (
                <div
                  key={prop.id}
                  onClick={() => setSelectedPropertyId(prop.id)}
                  style={{ cursor: 'pointer' }}
                >
                  <Card style={{ transition: 'transform 0.1s ease', hover: { transform: 'scale(1.01)' } } as any}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                      <div style={{ flex: 1, paddingRight: 8 }}>
                        <h2 style={{ fontSize: 16, fontWeight: 700, color: '#1e293b', margin: 0 }}>
                          {prop.name}
                        </h2>
                        {prop.address ? (
                          <p style={{ fontSize: 13, color: '#64748b', marginTop: 3, marginBottom: 0 }}>
                            📍 {prop.address}
                          </p>
                        ) : null}
                        <div style={{ fontSize: 12, color: '#475569', marginTop: 8, display: 'flex', gap: 8 }}>
                          <span><strong>{prop.unit_count}</strong> units</span>
                          <span>·</span>
                          <span style={{ color: '#15803d' }}><strong>{prop.occupied_count}</strong> occupied</span>
                          <span>·</span>
                          <span style={{ color: prop.vacant_count > 0 ? '#b91c1c' : '#64748b' }}>
                            <strong>{prop.vacant_count}</strong> vacant
                          </span>
                        </div>
                      </div>
                      <span style={{ fontSize: 18, color: '#94a3b8' }}>›</span>
                    </div>
                  </Card>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ======================================================== */}
      {/* MODAL: CREATE PROPERTY                                   */}
      {/* ======================================================== */}
      <Modal
        isOpen={isCreatePropertyOpen}
        onClose={() => setIsCreatePropertyOpen(false)}
        title="Add New Property"
      >
        <form onSubmit={handleCreateProperty}>
          <Input
            label="Property Name *"
            value={propertyName}
            onChange={(e) => setPropertyName(e.target.value)}
            placeholder="e.g. Shree Residency, Royal Palms"
            required
            maxLength={100}
            error={propertyFormError}
          />
          <Input
            label="Address (Optional)"
            value={propertyAddress}
            onChange={(e) => setPropertyAddress(e.target.value)}
            placeholder="e.g. 123, MG Road, Pune"
          />
          <Input
            label="Notes (Optional)"
            value={propertyNotes}
            onChange={(e) => setPropertyNotes(e.target.value)}
            placeholder="e.g. Near metro station"
          />
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreatePropertyOpen(false)}
              disabled={propertyFormLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={propertyFormLoading}>
              Create Property
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL: EDIT PROPERTY                                     */}
      {/* ======================================================== */}
      <Modal
        isOpen={isEditPropertyOpen}
        onClose={() => setIsEditPropertyOpen(false)}
        title="Edit Property"
      >
        <form onSubmit={handleEditProperty}>
          <Input
            label="Property Name *"
            value={propertyName}
            onChange={(e) => setPropertyName(e.target.value)}
            required
            maxLength={100}
            error={propertyFormError}
          />
          <Input
            label="Address"
            value={propertyAddress}
            onChange={(e) => setPropertyAddress(e.target.value)}
          />
          <Input
            label="Notes"
            value={propertyNotes}
            onChange={(e) => setPropertyNotes(e.target.value)}
          />
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsEditPropertyOpen(false)}
              disabled={propertyFormLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={propertyFormLoading}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* CONFIRM DIALOG: ARCHIVE PROPERTY                         */}
      {/* ======================================================== */}
      <ConfirmDialog
        isOpen={isArchivePropertyOpen}
        onClose={() => setIsArchivePropertyOpen(false)}
        onConfirm={handleArchiveProperty}
        title={`Archive ${propertyDetail?.name || 'Property'}?`}
        message="Archived properties won't appear in active property lists or generate new monthly rent records. All past tenant, unit, and payment history is preserved."
        confirmText="Archive Property"
        isDanger={true}
        loading={propertyFormLoading}
      />

      {/* ======================================================== */}
      {/* MODAL: CREATE UNIT                                       */}
      {/* ======================================================== */}
      <Modal
        isOpen={isCreateUnitOpen}
        onClose={() => setIsCreateUnitOpen(false)}
        title="Add Unit"
      >
        <form onSubmit={handleCreateUnit}>
          <Input
            label="Unit Number / Name *"
            value={unitName}
            onChange={(e) => setUnitName(e.target.value)}
            placeholder="e.g. 101, Flat 2B, Room 3"
            required
            maxLength={50}
            error={unitFormError}
          />
          <Select
            label="Unit Type *"
            value={unitType}
            onChange={(e) => setUnitType(e.target.value as UnitType)}
            options={UNIT_TYPE_OPTIONS}
          />
          <Input
            label="Monthly Rent (₹) *"
            type="number"
            min="1"
            step="1"
            value={unitRentRupees}
            onChange={(e) => setUnitRentRupees(e.target.value)}
            placeholder="e.g. 8000"
            required
            helperText="Enter rent in rupees (stored as integer paise)."
          />
          <Input
            label="Rent Due Day of Month (1–28) *"
            type="number"
            min="1"
            max="28"
            value={unitDueDay}
            onChange={(e) => setUnitDueDay(e.target.value)}
            required
            helperText="Strictly 1–28 to handle all months safely."
          />
          <Input
            label="Notes (Optional)"
            value={unitNotes}
            onChange={(e) => setUnitNotes(e.target.value)}
            placeholder="e.g. Ground floor, includes parking"
          />
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setIsCreateUnitOpen(false)}
              disabled={unitFormLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={unitFormLoading}>
              Add Unit
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL: EDIT UNIT                                         */}
      {/* ======================================================== */}
      <Modal
        isOpen={Boolean(editingUnit)}
        onClose={() => setEditingUnit(null)}
        title={`Edit Unit ${editingUnit?.name || ''}`}
      >
        <form onSubmit={handleEditUnit}>
          <Input
            label="Unit Number / Name *"
            value={unitName}
            onChange={(e) => setUnitName(e.target.value)}
            required
            maxLength={50}
            error={unitFormError}
          />
          <Select
            label="Unit Type *"
            value={unitType}
            onChange={(e) => setUnitType(e.target.value as UnitType)}
            options={UNIT_TYPE_OPTIONS}
          />
          <Input
            label="Monthly Rent (₹) *"
            type="number"
            min="1"
            step="1"
            value={unitRentRupees}
            onChange={(e) => setUnitRentRupees(e.target.value)}
            required
            helperText="Changes apply to future rent records only."
          />
          <Input
            label="Rent Due Day of Month (1–28) *"
            type="number"
            min="1"
            max="28"
            value={unitDueDay}
            onChange={(e) => setUnitDueDay(e.target.value)}
            required
            helperText="Changes apply to future rent records only."
          />
          <Input
            label="Notes"
            value={unitNotes}
            onChange={(e) => setUnitNotes(e.target.value)}
          />
          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 20 }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setEditingUnit(null)}
              disabled={unitFormLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={unitFormLoading}>
              Save Changes
            </Button>
          </div>
        </form>
      </Modal>

      {/* ======================================================== */}
      {/* CONFIRM DIALOG: ARCHIVE UNIT                             */}
      {/* ======================================================== */}
      <ConfirmDialog
        isOpen={Boolean(archivingUnit)}
        onClose={() => setArchivingUnit(null)}
        onConfirm={handleArchiveUnit}
        title={`Archive Unit ${archivingUnit?.name || ''}?`}
        message="This unit will be archived and will no longer appear as active. All historical rent records and payment transactions are preserved."
        confirmText="Archive Unit"
        isDanger={true}
        loading={unitFormLoading}
      />

      {/* ======================================================== */}
      {/* MODAL: ASSIGN TENANT TO VACANT UNIT                      */}
      {/* ======================================================== */}
      <Modal
        isOpen={Boolean(assigningUnit)}
        onClose={() => setAssigningUnit(null)}
        title={`Add Tenant to Unit ${assigningUnit?.name || ''}`}
      >
        <form onSubmit={handleCreateTenantForUnit} style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {tenantFormError && (
            <div style={{ color: '#dc2626', fontSize: 13, backgroundColor: '#fef2f2', padding: 8, borderRadius: 6 }}>
              {tenantFormError}
            </div>
          )}

          <Input
            label="Tenant Full Name *"
            value={tenantName}
            onChange={(e) => setTenantName(e.target.value)}
            placeholder="e.g. Rahul Patil"
            required
            disabled={tenantFormLoading}
          />

          <Input
            label="Phone Number *"
            type="tel"
            value={tenantPhone}
            onChange={(e) => setTenantPhone(e.target.value)}
            placeholder="10-digit mobile number"
            required
            disabled={tenantFormLoading}
          />

          <Input
            label="Email Address (Optional)"
            type="email"
            value={tenantEmail}
            onChange={(e) => setTenantEmail(e.target.value)}
            placeholder="tenant@example.com"
            disabled={tenantFormLoading}
          />

          <Input
            label="Move-In Date *"
            type="date"
            value={tenantMoveInDate}
            onChange={(e) => setTenantMoveInDate(e.target.value)}
            required
            disabled={tenantFormLoading}
          />

          <Input
            label="Security Deposit (₹)"
            type="number"
            value={tenantDepositRupees}
            onChange={(e) => setTenantDepositRupees(e.target.value)}
            min="0"
            disabled={tenantFormLoading}
          />

          <Input
            label="Notes (Optional)"
            value={tenantNotes}
            onChange={(e) => setTenantNotes(e.target.value)}
            placeholder="Agreement notes, identity info..."
            disabled={tenantFormLoading}
          />

          <div style={{ display: 'flex', gap: 10, justifyContent: 'flex-end', marginTop: 16 }}>
            <Button
              type="button"
              variant="secondary"
              onClick={() => setAssigningUnit(null)}
              disabled={tenantFormLoading}
            >
              Cancel
            </Button>
            <Button type="submit" variant="primary" loading={tenantFormLoading}>
              Assign Tenant
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
};
