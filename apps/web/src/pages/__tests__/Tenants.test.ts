import { describe, it, expect } from 'vitest';

describe('Tenant Management & Lifecycle Logic (Web)', () => {
  const INDIAN_PHONE_REGEX = /^(\+91[\-\s]?)?[6789]\d{9}$/;

  it('strictly validates Indian phone number format per backend contract', () => {
    // Valid numbers
    expect(INDIAN_PHONE_REGEX.test('9876543210')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('8123456789')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('7000000000')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('6999999999')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('+919876543210')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('+91 9876543210')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('+91-9876543210')).toBe(true);

    // Invalid numbers
    expect(INDIAN_PHONE_REGEX.test('5123456789')).toBe(false); // starts with 5
    expect(INDIAN_PHONE_REGEX.test('1234567890')).toBe(false); // starts with 1
    expect(INDIAN_PHONE_REGEX.test('987654321')).toBe(false); // 9 digits
    expect(INDIAN_PHONE_REGEX.test('98765432100')).toBe(false); // 11 digits
    expect(INDIAN_PHONE_REGEX.test('+19876543210')).toBe(false); // US prefix
    expect(INDIAN_PHONE_REGEX.test('abcdefghij')).toBe(false);
    expect(INDIAN_PHONE_REGEX.test('')).toBe(false);
  });

  it('validates tenant name length constraints (2 to 100 characters)', () => {
    const validateTenantName = (name: string): string | null => {
      const trimmed = name.trim();
      if (!trimmed || trimmed.length < 2) return 'Tenant name must be at least 2 characters.';
      if (trimmed.length > 100) return 'Tenant name must be at most 100 characters.';
      return null;
    };

    expect(validateTenantName('')).toBe('Tenant name must be at least 2 characters.');
    expect(validateTenantName('A')).toBe('Tenant name must be at least 2 characters.');
    expect(validateTenantName('   ')).toBe('Tenant name must be at least 2 characters.');
    expect(validateTenantName('Rahul Patil')).toBeNull();
    expect(validateTenantName('Priya Shah')).toBeNull();
    expect(validateTenantName('A'.repeat(101))).toBe('Tenant name must be at most 100 characters.');
  });

  it('converts security deposit rupees to integer paise without floating point error', () => {
    const convertDepositToPaise = (rupeesStr: string): number => {
      const num = parseFloat(rupeesStr);
      if (isNaN(num) || num < 0) throw new Error('Invalid deposit');
      return Math.round(num * 100);
    };

    expect(convertDepositToPaise('0')).toBe(0);
    expect(convertDepositToPaise('10000')).toBe(1000000);
    expect(convertDepositToPaise('25000.50')).toBe(2500050);
    expect(() => convertDepositToPaise('-500')).toThrow();
    expect(() => convertDepositToPaise('invalid')).toThrow();
  });

  it('filters only vacant and non-archived units for tenant assignment', () => {
    const sampleUnits = [
      { id: 'u1', name: '101', is_occupied: false, archived_at: null },
      { id: 'u2', name: '102', is_occupied: true, archived_at: null },
      { id: 'u3', name: '103', is_occupied: false, archived_at: '2026-09-01T00:00:00Z' },
      { id: 'u4', name: '104', is_occupied: false, archived_at: null },
    ];

    const eligible = sampleUnits.filter((u) => !u.is_occupied && !u.archived_at);
    expect(eligible.map((u) => u.name)).toEqual(['101', '104']);
  });

  it('calculates remaining rent balance accurately from expected and total paid paise', () => {
    const calculateRemaining = (expectedPaise: number, totalPaidPaise: number): number => {
      return Math.max(0, expectedPaise - totalPaidPaise);
    };

    expect(calculateRemaining(800000, 0)).toBe(800000);
    expect(calculateRemaining(800000, 500000)).toBe(300000);
    expect(calculateRemaining(800000, 800000)).toBe(0);
    expect(calculateRemaining(800000, 900000)).toBe(0);
  });

  it('correctly maps 409 conflict and 404 not found errors', () => {
    const mapTenantError = (status: number, code?: string): string => {
      if (status === 409 || code === 'UNIT_OCCUPIED') {
        return 'This unit already has an active tenant. Refreshing vacant units...';
      }
      if (status === 404) {
        return 'The requested tenant could not be found.';
      }
      return 'An unexpected error occurred.';
    };

    expect(mapTenantError(409, 'UNIT_OCCUPIED')).toContain('already has an active tenant');
    expect(mapTenantError(404)).toContain('could not be found');
    expect(mapTenantError(500)).toBe('An unexpected error occurred.');
  });
});
