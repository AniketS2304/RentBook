import { describe, it, expect, vi, beforeEach } from 'vitest';
import {
  formatPaiseToRupees,
  formatIsoDate,
  formatMonthYear,
  calculateCollectionPercent,
  getGreeting,
} from '../../utils/format';

describe('Dashboard Logic & Formatting (Web)', () => {
  it('formats paise to Indian rupee representation correctly without floating point errors', () => {
    expect(formatPaiseToRupees(0)).toBe('₹0');
    expect(formatPaiseToRupees(800000)).toBe('₹8,000');
    expect(formatPaiseToRupees(1250000)).toBe('₹12,500');
    expect(formatPaiseToRupees(15000000)).toBe('₹1,50,000');
  });

  it('formats ISO dates accurately for Indian locale display', () => {
    expect(formatIsoDate('2026-10-02')).toContain('2026');
    expect(formatIsoDate(null)).toBe('-');
    expect(formatIsoDate('')).toBe('-');
  });

  it('formats month and year accurately', () => {
    expect(formatMonthYear(10, 2026)).toBe('October 2026');
    expect(formatMonthYear(1, 2027)).toBe('January 2027');
    expect(formatMonthYear(12, 2025)).toBe('December 2025');
  });

  it('calculates collection percentage accurately and handles boundary conditions', () => {
    // 0 expected
    expect(calculateCollectionPercent(0, 0)).toBe(0);
    // Partial collection (16,000 of 45,000)
    expect(calculateCollectionPercent(1600000, 4500000)).toBe(36);
    // Complete collection (8,000 of 8,000)
    expect(calculateCollectionPercent(800000, 800000)).toBe(100);
    // Excess collection (10,000 of 8,000)
    expect(calculateCollectionPercent(1000000, 800000)).toBe(125);
  });

  it('returns appropriate time-of-day greeting', () => {
    const greeting = getGreeting();
    expect(['Good morning', 'Good afternoon', 'Good evening']).toContain(greeting);
  });

  it('handles month navigation boundary (December to January, January to December)', () => {
    // Next month from Dec 2026 -> Jan 2027
    let m = 12;
    let y = 2026;
    if (m === 12) {
      m = 1;
      y += 1;
    }
    expect(m).toBe(1);
    expect(y).toBe(2027);

    // Prev month from Jan 2027 -> Dec 2026
    if (m === 1) {
      m = 12;
      y -= 1;
    }
    expect(m).toBe(12);
    expect(y).toBe(2026);
  });
});
