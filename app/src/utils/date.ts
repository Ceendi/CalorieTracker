import { format } from 'date-fns';

/**
 * Format date for API calls (YYYY-MM-DD)
 */
export function formatDateForApi(date: Date = new Date()): string {
  return format(date, 'yyyy-MM-dd');
}
