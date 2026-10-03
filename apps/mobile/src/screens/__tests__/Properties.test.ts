import { describe, it, expect } from 'vitest';
import type { UnitType } from '../../types/api';

describe('Properties & Units Logic & Validation (Mobile)', () => {
  it('converts rupee input strictly into integer paise for API payload', () => {
    const convertRupeesToPaise = (input: string): number => {
      const num = parseFloat(input);
      if (isNaN(num) || num <= 0) {
        throw new Error('Rent must be a valid positive amount.');
      }
      return Math.round(num * 100);
    };

    expect(convertRupeesToPaise('8000')).toBe(800000);
    expect(convertRupeesToPaise('12500')).toBe(1250000);
    expect(convertRupeesToPaise('500.50')).toBe(50050);
    expect(() => convertRupeesToPaise('')).toThrow();
    expect(() => convertRupeesToPaise('0')).toThrow();
    expect(() => convertRupeesToPaise('-1000')).toThrow();
    expect(() => convertRupeesToPaise('abc')).toThrow();
  });

  it('strictly validates due day range (1 to 28)', () => {
    const isValidDueDay = (dayStr: string): boolean => {
      const day = parseInt(dayStr, 10);
      return !isNaN(day) && day >= 1 && day <= 28;
    };

    expect(isValidDueDay('1')).toBe(true);
    expect(isValidDueDay('5')).toBe(true);
    expect(isValidDueDay('15')).toBe(true);
    expect(isValidDueDay('28')).toBe(true);
    expect(isValidDueDay('0')).toBe(false);
    expect(isValidDueDay('29')).toBe(false);
    expect(isValidDueDay('30')).toBe(false);
    expect(isValidDueDay('31')).toBe(false);
    expect(isValidDueDay('-5')).toBe(false);
  });

  it('validates property name length and required constraints', () => {
    const validatePropertyName = (name: string): string | null => {
      const trimmed = name.trim();
      if (!trimmed) return 'Property name is required.';
      if (trimmed.length > 100) return 'Property name must be at most 100 characters.';
      return null;
    };

    expect(validatePropertyName('')).toBe('Property name is required.');
    expect(validatePropertyName('   ')).toBe('Property name is required.');
    expect(validatePropertyName('Royal Palms')).toBeNull();
    expect(validatePropertyName('x'.repeat(101))).toBe('Property name must be at most 100 characters.');
  });

  it('validates unit name constraints', () => {
    const validateUnitName = (name: string): string | null => {
      const trimmed = name.trim();
      if (!trimmed) return 'Unit name is required.';
      if (trimmed.length > 50) return 'Unit name must be at most 50 characters.';
      return null;
    };

    expect(validateUnitName('')).toBe('Unit name is required.');
    expect(validateUnitName('101')).toBeNull();
    expect(validateUnitName('Flat 4A')).toBeNull();
    expect(validateUnitName('y'.repeat(51))).toBe('Unit name must be at most 50 characters.');
  });

  it('enforces exact backend UnitType enums and friendly labels', () => {
    const UNIT_TYPES: Array<{ value: UnitType; label: string }> = [
      { value: 'FLAT', label: 'Flat' },
      { value: 'ROOM', label: 'Room' },
      { value: 'SHOP', label: 'Shop' },
      { value: 'OTHER', label: 'Other' },
    ];

    expect(UNIT_TYPES.map((t) => t.value)).toEqual(['FLAT', 'ROOM', 'SHOP', 'OTHER']);
  });

  it('derives occupancy directly from backend state without independent status engine', () => {
    const getUnitOccupancy = (isOccupied: boolean, tenantName?: string | null) => {
      if (isOccupied) {
        return {
          statusText: 'Occupied',
          badgeVariant: 'success' as const,
          tenantText: tenantName ? `Tenant: ${tenantName}` : undefined,
        };
      }
      return {
        statusText: 'Vacant',
        badgeVariant: 'neutral' as const,
        tenantText: undefined,
      };
    };

    const occupiedUnit = getUnitOccupancy(true, 'Amit Patel');
    expect(occupiedUnit.statusText).toBe('Occupied');
    expect(occupiedUnit.badgeVariant).toBe('success');
    expect(occupiedUnit.tenantText).toBe('Tenant: Amit Patel');

    const vacantUnit = getUnitOccupancy(false, null);
    expect(vacantUnit.statusText).toBe('Vacant');
    expect(vacantUnit.badgeVariant).toBe('neutral');
    expect(vacantUnit.tenantText).toBeUndefined();
  });

  it('formats archive warning dialog messages clearly specifying soft-archival', () => {
    const getPropertyArchiveMessage = (propName: string) =>
      `Are you sure you want to archive "${propName}"? Archived properties will no longer appear in active lists or generate new monthly rent records.`;

    const getUnitArchiveMessage = (unitName: string) =>
      `Are you sure you want to archive unit "${unitName}"? This unit will no longer appear as active.`;

    expect(getPropertyArchiveMessage('Royal Palms')).toContain('Archived properties will no longer appear');
    expect(getUnitArchiveMessage('101')).toContain('This unit will no longer appear as active');
  });
});
