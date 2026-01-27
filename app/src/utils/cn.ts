import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merge Tailwind CSS classes with proper precedence.
 * Uses clsx for conditional classes and tailwind-merge to handle conflicts.
 *
 * @example
 * cn("bg-red-500", "bg-blue-500") // => "bg-blue-500"
 * cn("p-4", isActive && "bg-primary", disabled && "opacity-50")
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
