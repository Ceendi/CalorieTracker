export type GLLabel = 'niski' | 'średni' | 'wysoki';

export interface GLResult {
  value: number;
  label: GLLabel;
}

/**
 * Calculate glycemic load for a portion.
 * GL = (GI × carbs_grams) / 100
 *
 * Classification (Harvard School of Public Health):
 *   ≤ 10  → low
 *   11–19 → medium
 *   ≥ 20  → high
 */
export function calculateGL(gi: number, carbsGrams: number): GLResult {
  const gl = (gi * carbsGrams) / 100;
  const value = Math.round(gl * 10) / 10;
  const label: GLLabel = value <= 10 ? 'niski' : value <= 19 ? 'średni' : 'wysoki';
  return { value, label };
}
