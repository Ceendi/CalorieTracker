import { format } from 'date-fns';

/**
 * Format date for API calls (YYYY-MM-DD)
 */
export function formatDateForApi(date: Date = new Date()): string {
  return format(date, 'yyyy-MM-dd');
}

/**
 * Format a date for display with locale support
 */
export function formatDisplayDate(date: Date, locale: string = 'en'): string {
  return date.toLocaleDateString(locale === 'pl' ? 'pl-PL' : 'en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric',
  });
}

/**
 * Format a number with locale-specific formatting
 */
export function formatNumber(value: number, locale: string = 'en'): string {
  return new Intl.NumberFormat(locale === 'pl' ? 'pl-PL' : 'en-US').format(value);
}
