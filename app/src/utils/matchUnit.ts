import { UnitInfo } from '@/types/food';

export function matchUnit(
  label: string,
  units: UnitInfo[] | undefined,
  estimatedGramsPerUnit?: number
): UnitInfo | null {
  if (!units || units.length === 0 || !label) return null;

  const lower = label.toLowerCase();

  const exact = units.find(u => u.label.toLowerCase() === lower);
  if (exact) return exact;

  const candidates = units.filter(u => u.label.toLowerCase().startsWith(lower));
  if (candidates.length === 0) return null;
  if (candidates.length === 1) return candidates[0];

  if (estimatedGramsPerUnit && estimatedGramsPerUnit > 0) {
    return candidates.reduce((best, c) =>
      Math.abs(c.grams - estimatedGramsPerUnit) < Math.abs(best.grams - estimatedGramsPerUnit) ? c : best
    );
  }

  return candidates[0];
}

