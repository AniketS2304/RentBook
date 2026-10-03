/**
 * Utility functions for RentBook mobile client.
 * Note: Domain rule requires all money to remain paise numbers in state/API,
 * and be formatted to rupees only at the display layer.
 */

export function formatPaiseToRupees(paise: number): string {
  const rupees = Math.floor(paise / 100);
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
