/**
 * Formatting utilities for RentBook Mobile.
 * Money remains in integer paise until rendered.
 */

const MONTH_NAMES = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December'
];

export function formatPaiseToRupees(paise: number): string {
  const rupees = Math.floor((paise || 0) / 100);
  return `₹${rupees.toLocaleString('en-IN')}`;
}

export function formatIsoDate(dateString?: string | null): string {
  if (!dateString) return '-';
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  } catch {
    return dateString;
  }
}

export function formatMonthYear(month: number, year: number): string {
  const monthName = MONTH_NAMES[month - 1] || `Month ${month}`;
  return `${monthName} ${year}`;
}

export function getGreeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return 'Good morning';
  if (hour < 17) return 'Good afternoon';
  return 'Good evening';
}

export function calculateCollectionPercent(collectedPaise: number, expectedPaise: number): number {
  if (!expectedPaise || expectedPaise <= 0) return 0;
  const pct = Math.round((collectedPaise / expectedPaise) * 100);
  return Math.max(0, pct);
}
