import { describe, it, expect } from 'vitest';
import {
  formatPaiseToRupees,
  formatIsoDate,
  formatMonthYear,
  calculateCollectionPercent,
  getGreeting,
} from '../../utils/format';

describe('Dashboard Logic & Formatting (Mobile)', () => {
  it('formats paise to Indian rupee representation without floats', () => {
    expect(formatPaiseToRupees(0)).toBe('₹0');
    expect(formatPaiseToRupees(800000)).toBe('₹8,000');
    expect(formatPaiseToRupees(1500000)).toBe('₹15,000');
    expect(formatPaiseToRupees(25000000)).toBe('₹2,50,000');
  });

  it('formats ISO dates correctly', () => {
    expect(formatIsoDate('2026-10-01')).toContain('2026');
    expect(formatIsoDate(null)).toBe('-');
  });

  it('formats month and year accurately', () => {
    expect(formatMonthYear(10, 2026)).toBe('October 2026');
    expect(formatMonthYear(12, 2025)).toBe('December 2025');
  });

  it('calculates collection percentage accurately', () => {
    expect(calculateCollectionPercent(0, 0)).toBe(0);
    expect(calculateCollectionPercent(1600000, 4500000)).toBe(36);
    expect(calculateCollectionPercent(800000, 800000)).toBe(100);
    expect(calculateCollectionPercent(1200000, 800000)).toBe(150);
  });

  it('returns valid greeting', () => {
    const greeting = getGreeting();
    expect(['Good morning', 'Good afternoon', 'Good evening']).toContain(greeting);
  });
});
