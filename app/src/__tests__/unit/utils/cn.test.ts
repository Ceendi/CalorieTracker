import { cn } from '../../../utils/cn';

describe('cn', () => {
  it('merges class names', () => {
    expect(cn('px-4', 'py-2')).toBe('px-4 py-2');
  });

  it('resolves Tailwind conflicts (last wins)', () => {
    expect(cn('bg-red-500', 'bg-blue-500')).toBe('bg-blue-500');
  });

  it('handles conditional classes', () => {
    const isActive = true;
    const isDisabled = false;
    const result = cn('base', isActive && 'active', isDisabled && 'disabled');
    expect(result).toContain('base');
    expect(result).toContain('active');
    expect(result).not.toContain('disabled');
  });

  it('handles undefined and null', () => {
    expect(cn('base', undefined, null)).toBe('base');
  });

  it('handles empty string', () => {
    expect(cn('')).toBe('');
  });

  it('handles array input', () => {
    expect(cn(['px-4', 'py-2'])).toBe('px-4 py-2');
  });
});
