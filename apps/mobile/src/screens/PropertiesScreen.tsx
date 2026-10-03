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
  Modal,
  ConfirmDialog,
  Skeleton,
  EmptyState,
  ErrorState,
} from '../components/UI';

const UNIT_TYPE_OPTIONS: Array<{ value: UnitType; label: string }> = [
  { value: 'FLAT', label: 'Flat' },
  { value: 'ROOM', label: 'Room' },
  { value: 'SHOP', label: 'Shop' },
  { value: 'OTHER', label: 'Other' },
];

export const PropertiesScreen: React.FC = () => {
  // Navigation / Active View
  const [selectedPropertyId, setSelectedPropertyId] = useState<string | null>(null);

  // Data states
  const [properties, setProperties] = useState<PropertyListItem[]>([]);
  const [propertyDetail, setPropertyDetail] = useState<PropertyDetail | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

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

  const handleCreateTenantForUnit = async () => {
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
      setTenantFormError('Deposit must be a valid non-negative amount.');
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
      Alert.alert('Success', `Tenant "${nameTrimmed}" assigned to Unit ${assigningUnit.name}!`);
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

  const handleCreateProperty = async () => {
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

  const handleEditProperty = async () => {
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
      setSelectedPropertyId(null);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to archive property.');
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

  const handleCreateUnit = async () => {
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

  const handleEditUnit = async () => {
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
      setArchivingUnit(null);
      loadPropertyDetail(propertyDetail.id);
    } catch (err: any) {
      Alert.alert('Error', err.message || 'Failed to archive unit.');
    } finally {
      setUnitFormLoading(false);
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      {/* ======================================================== */}
      {/* VIEW: PROPERTY DETAIL (when a property is selected)     */}
      {/* ======================================================== */}
      {selectedPropertyId ? (
        <View style={styles.contentColumn}>
          {/* Back button & Action buttons */}
          <View style={styles.detailHeaderRow}>
            <TouchableOpacity
              onPress={() => setSelectedPropertyId(null)}
              style={styles.backButton}
            >
              <Text style={styles.backButtonText}>← All Properties</Text>
            </TouchableOpacity>
            <View style={{ flexDirection: 'row', gap: 8 }}>
              <Button
                title="Edit"
                size="sm"
                variant="outline"
                onPress={handleOpenEditProperty}
              />
              <Button
                title="Archive"
                size="sm"
                variant="danger"
                onPress={() => setIsArchivePropertyOpen(true)}
              />
            </View>
          </View>

          {loading && (
            <View style={{ gap: 12 }}>
              <Skeleton height={32} width="60%" />
              <Skeleton height={20} width="40%" />
              <View style={{ flexDirection: 'row', gap: 8 }}>
                <Skeleton height={70} width="31%" />
                <Skeleton height={70} width="31%" />
                <Skeleton height={70} width="31%" />
              </View>
            </View>
          )}

          {error && !loading && (
            <ErrorState
              message={error}
              onRetry={() => loadPropertyDetail(selectedPropertyId)}
            />
          )}

          {!loading && propertyDetail && (
            <View style={styles.contentColumn}>
              {/* Property Info Card */}
              <Card>
                <Text style={styles.propertyName}>{propertyDetail.name}</Text>
                {propertyDetail.address ? (
                  <Text style={styles.propertyAddress}>📍 {propertyDetail.address}</Text>
                ) : null}
                {propertyDetail.notes ? (
                  <Text style={styles.propertyNotes}>"{propertyDetail.notes}"</Text>
                ) : null}

                {/* Stats Row */}
                <View style={styles.statsRow}>
                  <View style={[styles.statBox, { backgroundColor: '#f8fafc', borderColor: '#e2e8f0' }]}>
                    <Text style={styles.statLabel}>TOTAL</Text>
                    <Text style={[styles.statCount, { color: '#0f172a' }]}>{propertyDetail.unit_count}</Text>
                  </View>
                  <View style={[styles.statBox, { backgroundColor: '#f0fdf4', borderColor: '#bbf7d0' }]}>
                    <Text style={[styles.statLabel, { color: '#16a34a' }]}>OCCUPIED</Text>
                    <Text style={[styles.statCount, { color: '#15803d' }]}>{propertyDetail.occupied_count}</Text>
                  </View>
                  <View style={[styles.statBox, { backgroundColor: '#fef2f2', borderColor: '#fecaca' }]}>
                    <Text style={[styles.statLabel, { color: '#dc2626' }]}>VACANT</Text>
                    <Text style={[styles.statCount, { color: '#b91c1c' }]}>{propertyDetail.vacant_count}</Text>
                  </View>
                </View>
              </Card>

              {/* Units Header + Add Unit Button */}
              <View style={styles.unitsHeaderRow}>
                <Text style={styles.sectionTitle}>
                  Units ({propertyDetail.units.length})
                </Text>
                <Button
                  title="+ Add Unit"
                  size="sm"
                  onPress={handleOpenCreateUnit}
                />
              </View>

              {/* Units List */}
              {propertyDetail.units.length === 0 ? (
                <EmptyState
                  title="No units added yet"
                  description="Add flats, rooms, or shops to this property to track tenants and rent."
                  actionLabel="+ Add First Unit"
                  onAction={handleOpenCreateUnit}
                  icon="🚪"
                />
              ) : (
                <View style={{ gap: 10 }}>
                  {propertyDetail.units.map((unit) => (
                    <Card key={unit.id} style={{ padding: 14 }}>
                      <View style={styles.unitRow}>
                        <View style={{ flex: 1 }}>
                          <View style={{ flexDirection: 'row', alignItems: 'center', gap: 6 }}>
                            <Text style={styles.unitTitle}>{unit.name}</Text>
                            <Badge status={unit.unit_type} />
                          </View>
                          <Text style={styles.unitRent}>
                            {formatPaiseToRupees(unit.monthly_rent_paise)}{' '}
                            <Text style={styles.unitDue}>/ month · Due on {unit.rent_due_day}th</Text>
                          </Text>
                          {unit.notes ? (
                            <Text style={styles.unitNotesText}>{unit.notes}</Text>
                          ) : null}
                        </View>

                        <View style={{ alignItems: 'flex-end', gap: 6 }}>
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
                          <View style={{ flexDirection: 'row', gap: 8, marginTop: 4 }}>
                            {!unit.is_occupied && (
                              <>
                                <TouchableOpacity onPress={() => handleOpenAssignTenant(unit)}>
                                  <Text style={[styles.editActionText, { color: '#16a34a' }]}>+ Add Tenant</Text>
                                </TouchableOpacity>
                                <Text style={{ color: '#cbd5e1' }}>·</Text>
                              </>
                            )}
                            <TouchableOpacity onPress={() => handleOpenEditUnit(unit)}>
                              <Text style={styles.editActionText}>Edit</Text>
                            </TouchableOpacity>
                            <Text style={{ color: '#cbd5e1' }}>·</Text>
                            <TouchableOpacity onPress={() => setArchivingUnit(unit)}>
                              <Text style={styles.archiveActionText}>Archive</Text>
                            </TouchableOpacity>
                          </View>
                        </View>
                      </View>
                    </Card>
                  ))}
                </View>
              )}
            </View>
          )}
        </View>
      ) : (
        /* ======================================================== */
        /* VIEW: PROPERTIES LIST                                    */
        /* ======================================================== */
        <View style={styles.contentColumn}>
          {/* Header & Add Button */}
          <View style={styles.listHeaderRow}>
            <View>
              <Text style={styles.screenTitle}>Properties</Text>
              <Text style={styles.screenSubtitle}>Manage buildings and complexes</Text>
            </View>
            <Button
              title="+ Add Property"
              size="sm"
              onPress={handleOpenCreateProperty}
            />
          </View>

          {loading && (
            <View style={{ gap: 10 }}>
              <Skeleton height={80} />
              <Skeleton height={80} />
              <Skeleton height={80} />
            </View>
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
            <View style={{ gap: 10 }}>
              {properties.map((prop) => (
                <TouchableOpacity
                  key={prop.id}
                  onPress={() => setSelectedPropertyId(prop.id)}
                  activeOpacity={0.8}
                >
                  <Card>
                    <View style={{ flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' }}>
                      <View style={{ flex: 1, paddingRight: 8 }}>
                        <Text style={styles.propCardName}>{prop.name}</Text>
                        {prop.address ? (
                          <Text style={styles.propCardAddress}>📍 {prop.address}</Text>
                        ) : null}
                        <View style={styles.propCardStats}>
                          <Text style={styles.statChip}>
                            <Text style={{ fontWeight: 'bold' }}>{prop.unit_count}</Text> units
                          </Text>
                          <Text style={{ color: '#94a3b8' }}>·</Text>
                          <Text style={[styles.statChip, { color: '#15803d' }]}>
                            <Text style={{ fontWeight: 'bold' }}>{prop.occupied_count}</Text> occupied
                          </Text>
                          <Text style={{ color: '#94a3b8' }}>·</Text>
                          <Text
                            style={[
                              styles.statChip,
                              { color: prop.vacant_count > 0 ? '#b91c1c' : '#64748b' },
                            ]}
                          >
                            <Text style={{ fontWeight: 'bold' }}>{prop.vacant_count}</Text> vacant
                          </Text>
                        </View>
                      </View>
                      <Text style={styles.arrowIcon}>›</Text>
                    </View>
                  </Card>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      )}

      {/* ======================================================== */}
      {/* MODAL: CREATE PROPERTY                                   */}
      {/* ======================================================== */}
      <Modal
        isOpen={isCreatePropertyOpen}
        onClose={() => setIsCreatePropertyOpen(false)}
        title="Add New Property"
      >
        <Input
          label="Property Name *"
          value={propertyName}
          onChangeText={setPropertyName}
          placeholder="e.g. Shree Residency, Royal Palms"
          maxLength={100}
          error={propertyFormError}
        />
        <Input
          label="Address (Optional)"
          value={propertyAddress}
          onChangeText={setPropertyAddress}
          placeholder="e.g. 123, MG Road, Pune"
        />
        <Input
          label="Notes (Optional)"
          value={propertyNotes}
          onChangeText={setPropertyNotes}
          placeholder="e.g. Near metro station"
          multiline
        />
        <View style={styles.modalActionRow}>
          <Button
            title="Cancel"
            variant="secondary"
            onPress={() => setIsCreatePropertyOpen(false)}
            disabled={propertyFormLoading}
            style={{ flex: 1 }}
          />
          <Button
            title="Create Property"
            variant="primary"
            onPress={handleCreateProperty}
            loading={propertyFormLoading}
            style={{ flex: 1 }}
          />
        </View>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL: EDIT PROPERTY                                     */}
      {/* ======================================================== */}
      <Modal
        isOpen={isEditPropertyOpen}
        onClose={() => setIsEditPropertyOpen(false)}
        title="Edit Property"
      >
        <Input
          label="Property Name *"
          value={propertyName}
          onChangeText={setPropertyName}
          maxLength={100}
          error={propertyFormError}
        />
        <Input
          label="Address"
          value={propertyAddress}
          onChangeText={setPropertyAddress}
        />
        <Input
          label="Notes"
          value={propertyNotes}
          onChangeText={setPropertyNotes}
          multiline
        />
        <View style={styles.modalActionRow}>
          <Button
            title="Cancel"
            variant="secondary"
            onPress={() => setIsEditPropertyOpen(false)}
            disabled={propertyFormLoading}
            style={{ flex: 1 }}
          />
          <Button
            title="Save Changes"
            variant="primary"
            onPress={handleEditProperty}
            loading={propertyFormLoading}
            style={{ flex: 1 }}
          />
        </View>
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
        <Input
          label="Unit Number / Name *"
          value={unitName}
          onChangeText={setUnitName}
          placeholder="e.g. 101, Flat 2B, Room 3"
          maxLength={50}
          error={unitFormError}
        />

        {/* Unit Type Selection Chips */}
        <Text style={styles.fieldLabel}>Unit Type *</Text>
        <View style={styles.chipRow}>
          {UNIT_TYPE_OPTIONS.map((opt) => (
            <TouchableOpacity
              key={opt.value}
              onPress={() => setUnitType(opt.value)}
              style={[
                styles.typeChip,
                unitType === opt.value && styles.typeChipActive,
              ]}
            >
              <Text
                style={[
                  styles.typeChipText,
                  unitType === opt.value && styles.typeChipTextActive,
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Input
          label="Monthly Rent (₹) *"
          value={unitRentRupees}
          onChangeText={setUnitRentRupees}
          placeholder="e.g. 8000"
          keyboardType="numeric"
          helperText="Enter rent in rupees (stored as integer paise)."
        />
        <Input
          label="Rent Due Day of Month (1–28) *"
          value={unitDueDay}
          onChangeText={setUnitDueDay}
          keyboardType="numeric"
          maxLength={2}
          helperText="Strictly 1–28 to handle all months safely."
        />
        <Input
          label="Notes (Optional)"
          value={unitNotes}
          onChangeText={setUnitNotes}
          placeholder="e.g. Road facing, parking included"
        />

        <View style={styles.modalActionRow}>
          <Button
            title="Cancel"
            variant="secondary"
            onPress={() => setIsCreateUnitOpen(false)}
            disabled={unitFormLoading}
            style={{ flex: 1 }}
          />
          <Button
            title="Add Unit"
            variant="primary"
            onPress={handleCreateUnit}
            loading={unitFormLoading}
            style={{ flex: 1 }}
          />
        </View>
      </Modal>

      {/* ======================================================== */}
      {/* MODAL: EDIT UNIT                                         */}
      {/* ======================================================== */}
      <Modal
        isOpen={Boolean(editingUnit)}
        onClose={() => setEditingUnit(null)}
        title={`Edit Unit ${editingUnit?.name || ''}`}
      >
        <Input
          label="Unit Number / Name *"
          value={unitName}
          onChangeText={setUnitName}
          maxLength={50}
          error={unitFormError}
        />

        <Text style={styles.fieldLabel}>Unit Type *</Text>
        <View style={styles.chipRow}>
          {UNIT_TYPE_OPTIONS.map((opt) => (
            <TouchableOpacity
              key={opt.value}
              onPress={() => setUnitType(opt.value)}
              style={[
                styles.typeChip,
                unitType === opt.value && styles.typeChipActive,
              ]}
            >
              <Text
                style={[
                  styles.typeChipText,
                  unitType === opt.value && styles.typeChipTextActive,
                ]}
              >
                {opt.label}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        <Input
          label="Monthly Rent (₹) *"
          value={unitRentRupees}
          onChangeText={setUnitRentRupees}
          keyboardType="numeric"
          helperText="Changes apply to future rent records only."
        />
        <Input
          label="Rent Due Day of Month (1–28) *"
          value={unitDueDay}
          onChangeText={setUnitDueDay}
          keyboardType="numeric"
          maxLength={2}
          helperText="Changes apply to future rent records only."
        />
        <Input
          label="Notes"
          value={unitNotes}
          onChangeText={setUnitNotes}
        />

        <View style={styles.modalActionRow}>
          <Button
            title="Cancel"
            variant="secondary"
            onPress={() => setEditingUnit(null)}
            disabled={unitFormLoading}
            style={{ flex: 1 }}
          />
          <Button
            title="Save Changes"
            variant="primary"
            onPress={handleEditUnit}
            loading={unitFormLoading}
            style={{ flex: 1 }}
          />
        </View>
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
        <View style={{ gap: 12 }}>
          {tenantFormError && (
            <View style={{ backgroundColor: '#fef2f2', borderColor: '#fecaca', borderWidth: 1, padding: 10, borderRadius: 8 }}>
              <Text style={{ color: '#dc2626', fontSize: 13 }}>{tenantFormError}</Text>
            </View>
          )}

          <Input
            label="Tenant Full Name *"
            value={tenantName}
            onChangeText={setTenantName}
            placeholder="e.g. Rahul Patil"
            editable={!tenantFormLoading}
          />

          <Input
            label="Phone Number *"
            value={tenantPhone}
            onChangeText={setTenantPhone}
            placeholder="10-digit mobile number"
            keyboardType="phone-pad"
            editable={!tenantFormLoading}
          />

          <Input
            label="Email Address (Optional)"
            value={tenantEmail}
            onChangeText={setTenantEmail}
            placeholder="tenant@example.com"
            keyboardType="email-address"
            editable={!tenantFormLoading}
          />

          <Input
            label="Move-In Date (YYYY-MM-DD) *"
            value={tenantMoveInDate}
            onChangeText={setTenantMoveInDate}
            placeholder="YYYY-MM-DD"
            editable={!tenantFormLoading}
          />

          <Input
            label="Security Deposit (₹)"
            value={tenantDepositRupees}
            onChangeText={setTenantDepositRupees}
            placeholder="0"
            keyboardType="numeric"
            editable={!tenantFormLoading}
          />

          <Input
            label="Notes (Optional)"
            value={tenantNotes}
            onChangeText={setTenantNotes}
            placeholder="Identity proof, emergency contact..."
            editable={!tenantFormLoading}
          />

          <View style={{ flexDirection: 'row', gap: 8, marginTop: 8 }}>
            <Button
              title="Cancel"
              variant="outline"
              onPress={() => setAssigningUnit(null)}
              disabled={tenantFormLoading}
              style={{ flex: 1 }}
            />
            <Button
              title="Assign Tenant"
              variant="primary"
              onPress={handleCreateTenantForUnit}
              loading={tenantFormLoading}
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
    padding: 16,
    flexGrow: 1,
    backgroundColor: '#ffffff',
  },
  contentColumn: {
    gap: 14,
  },
  listHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  screenTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  screenSubtitle: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 2,
  },
  detailHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  backButton: {
    paddingVertical: 6,
  },
  backButtonText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  propertyName: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  propertyAddress: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 4,
  },
  propertyNotes: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 4,
    fontStyle: 'italic',
  },
  statsRow: {
    flexDirection: 'row',
    gap: 8,
    marginTop: 14,
  },
  statBox: {
    flex: 1,
    padding: 8,
    borderRadius: 8,
    borderWidth: 1,
    alignItems: 'center',
  },
  statLabel: {
    fontSize: 10,
    fontWeight: 'bold',
    color: '#64748b',
  },
  statCount: {
    fontSize: 16,
    fontWeight: 'bold',
    marginTop: 2,
  },
  unitsHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  unitRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  unitTitle: {
    fontSize: 15,
    fontWeight: 'bold',
    color: '#0f172a',
  },
  unitRent: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#1e293b',
    marginTop: 4,
  },
  unitDue: {
    fontSize: 12,
    fontWeight: 'normal',
    color: '#64748b',
  },
  unitNotesText: {
    fontSize: 12,
    color: '#64748b',
    marginTop: 2,
  },
  editActionText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#2563eb',
  },
  archiveActionText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#dc2626',
  },
  propCardName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#1e293b',
  },
  propCardAddress: {
    fontSize: 13,
    color: '#64748b',
    marginTop: 3,
  },
  propCardStats: {
    flexDirection: 'row',
    gap: 6,
    alignItems: 'center',
    marginTop: 8,
  },
  statChip: {
    fontSize: 12,
    color: '#475569',
  },
  arrowIcon: {
    fontSize: 20,
    color: '#94a3b8',
  },
  modalActionRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 16,
  },
  fieldLabel: {
    fontSize: 13,
    fontWeight: '600',
    color: '#334155',
    marginBottom: 6,
  },
  chipRow: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 14,
  },
  typeChip: {
    paddingHorizontal: 12,
    paddingVertical: 7,
    borderRadius: 8,
    backgroundColor: '#f1f5f9',
    borderWidth: 1,
    borderColor: '#e2e8f0',
  },
  typeChipActive: {
    backgroundColor: '#eff6ff',
    borderColor: '#2563eb',
  },
  typeChipText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#475569',
  },
  typeChipTextActive: {
    color: '#2563eb',
  },
});
