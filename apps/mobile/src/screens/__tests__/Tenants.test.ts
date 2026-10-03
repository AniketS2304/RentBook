import { describe, it, expect } from 'vitest';

describe('Tenant Management & Lifecycle Logic (Mobile)', () => {
  const INDIAN_PHONE_REGEX = /^(\+91[\-\s]?)?[6789]\d{9}$/;

  it('validates 10-digit Indian mobile numbers with optional +91 prefix', () => {
    expect(INDIAN_PHONE_REGEX.test('9876543210')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('6234567890')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('+919876543210')).toBe(true);
    expect(INDIAN_PHONE_REGEX.test('+91 9876543210')).toBe(true);

    expect(INDIAN_PHONE_REGEX.test('5876543210')).toBe(false); // starts with 5
    expect(INDIAN_PHONE_REGEX.test('98765')).toBe(false); // too short
    expect(INDIAN_PHONE_REGEX.test('+447876543210')).toBe(false); // UK prefix
  });

  it('validates tenant name requirements', () => {
    const validateName = (name: string): string | null => {
      const trimmed = name.trim();
      if (!trimmed || trimmed.length < 2) return 'Tenant name must be at least 2 characters.';
      if (trimmed.length > 100) return 'Tenant name must be at most 100 characters.';
      return null;
    };

    expect(validateName('Amit Joshi')).toBeNull();
    expect(validateName('x')).toBe('Tenant name must be at least 2 characters.');
    expect(validateName('')).toBe('Tenant name must be at least 2 characters.');
    expect(validateName('z'.repeat(101))).toBe('Tenant name must be at most 100 characters.');
  });

  it('converts deposit to integer paise correctly', () => {
    const depositToPaise = (rupeesStr: string): number => {
      const num = parseFloat(rupeesStr);
      if (isNaN(num) || num < 0) throw new Error('Invalid deposit');
      return Math.round(num * 100);
    };

    expect(depositToPaise('0')).toBe(0);
    expect(depositToPaise('15000')).toBe(1500000);
    expect(depositToPaise('20000.50')).toBe(2000050);
  });

  it('distinguishes active and former tenant lifecycle badges', () => {
    const getLifecycleBadge = (status: string) => {
      if (status === 'ACTIVE') {
        return { label: 'ACTIVE', badgeStatus: 'PAID' };
      }
      return { label: 'FORMER', badgeStatus: 'VOID' };
    };

    expect(getLifecycleBadge('ACTIVE')).toEqual({ label: 'ACTIVE', badgeStatus: 'PAID' });
    expect(getLifecycleBadge('INACTIVE')).toEqual({ label: 'FORMER', badgeStatus: 'VOID' });
  });

  it('formats move out warning message and ensures history preservation text', () => {
    const formatMoveOutWarning = (tenantName: string, unitName: string) => {
      return `Move ${tenantName} out? Unit ${unitName} will become vacant for new tenancies while historical records remain preserved.`;
    };

    const warning = formatMoveOutWarning('Rahul Patil', '101');
    expect(warning).toContain('Rahul Patil');
    expect(warning).toContain('Unit 101');
    expect(warning).toContain('historical records remain preserved');
  });

  it('correctly filters tenants across tabs', () => {
    const list = [
      { id: '1', name: 'Rahul', status: 'ACTIVE' },
      { id: '2', name: 'Priya', status: 'ACTIVE' },
      { id: '3', name: 'Amit', status: 'INACTIVE' },
    ];

    const activeList = list.filter((t) => t.status === 'ACTIVE');
    const formerList = list.filter((t) => t.status === 'INACTIVE');

    expect(activeList.length).toBe(2);
    expect(formerList.length).toBe(1);
    expect(formerList[0].name).toBe('Amit');
  });
});
