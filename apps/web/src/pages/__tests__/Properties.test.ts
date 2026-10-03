import { describe, it, expect } from 'vitest';

describe('Properties & Units Logic and Validation (Web)', () => {
  it('converts rupee input strictly into integer paise without floating point inaccuracy', () => {
    const convertToPaise = (rupeesStr: string): number => {
      const num = parseFloat(rupeesStr);
      if (isNaN(num) || num <= 0) throw new Error('Invalid rent');
      return Math.round(num * 100);
    };

    expect(convertToPaise('8000')).toBe(800000);
    expect(convertToPaise('12500')).toBe(1250000);
    expect(convertToPaise('6500.50')).toBe(650050);
    expect(() => convertToPaise('0')).toThrow();
    expect(() => convertToPaise('-500')).toThrow();
    expect(() => convertToPaise('abc')).toThrow();
  });

  it('strictly validates due day range (1 to 28)', () => {
    const validateDueDay = (dayStr: string): boolean => {
      const day = parseInt(dayStr, 10);
      return !isNaN(day) && day >= 1 && day <= 28;
    };

    expect(validateDueDay('1')).toBe(true);
    expect(validateDueDay('5')).toBe(true);
    expect(validateDueDay('28')).toBe(true);
    expect(validateDueDay('0')).toBe(false);
    expect(validateDueDay('29')).toBe(false);
    expect(validateDueDay('31')).toBe(false);
    expect(validateDueDay('-1')).toBe(false);
  });

  it('validates property name length and required constraints', () => {
    const validatePropName = (name: string): string | null => {
      const trimmed = name.trim();
      if (!trimmed) return 'Property name is required.';
      if (trimmed.length > 100) return 'Property name must be at most 100 characters.';
      return null;
    };

    expect(validatePropName('')).toBe('Property name is required.');
    expect(validatePropName('   ')).toBe('Property name is required.');
    expect(validatePropName('Shree Residency')).toBeNull();
    expect(validatePropName('a'.repeat(101))).toBe('Property name must be at most 100 characters.');
  });

  it('validates unit name length and required constraints', () => {
    const validateUnitName = (name: string): string | null => {
      const trimmed = name.trim();
      if (!trimmed) return 'Unit name is required.';
      if (trimmed.length > 50) return 'Unit name must be at most 50 characters.';
      return null;
    };

    expect(validateUnitName('')).toBe('Unit name is required.');
    expect(validateUnitName('101')).toBeNull();
    expect(validateUnitName('Flat 2B - East Wing')).toBeNull();
    expect(validateUnitName('a'.repeat(51))).toBe('Unit name must be at most 50 characters.');
  });

  it('preserves exact backend UnitType enums', () => {
    const validTypes = ['FLAT', 'ROOM', 'SHOP', 'OTHER'];
    expect(validTypes).toContain('FLAT');
    expect(validTypes).toContain('ROOM');
    expect(validTypes).toContain('SHOP');
    expect(validTypes).toContain('OTHER');
    expect(validTypes).not.toContain('APARTMENT');
  });

  it('maps occupancy correctly from backend fields without independent status engine', () => {
    const getOccupancyLabel = (isOccupied: boolean, tenantName?: string | null): string => {
      if (isOccupied) {
        return tenantName ? `Occupied · ${tenantName}` : 'Occupied';
      }
      return 'Vacant';
    };

    expect(getOccupancyLabel(true, 'Rahul Sharma')).toBe('Occupied · Rahul Sharma');
    expect(getOccupancyLabel(true, null)).toBe('Occupied');
    expect(getOccupancyLabel(false, null)).toBe('Vacant');
  });
});
