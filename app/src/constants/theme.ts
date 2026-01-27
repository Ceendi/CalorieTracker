/**
 * Below are the colors that are used in the app. The colors are defined in the light and dark mode.
 * There are many other ways to style your app. For example, [Nativewind](https://www.nativewind.dev/), [Tamagui](https://tamagui.dev/), [unistyles](https://reactnativeunistyles.vercel.app), etc.
 */

import { Platform } from 'react-native';

const tintColorLight = '#4F46E5'; // Indigo-600
const tintColorDark = '#818cf8'; // Indigo-400

// Palette from global.css
// Light: background=#f8fafc, foreground=#020617, card=#ffffff, primary=#4f46e5, muted=#f1f5f9, muted-foreground=#64748b, border=#e2e8f0
// Dark: background=#0f172a, foreground=#f8fafc, card=#1e293b, primary=#4f46e5, muted=#1e293b, muted-foreground=#94a3b8, border=#1e293b

export const Colors = {
  light: {
    text: '#020617', // foreground
    background: '#f8fafc',
    tint: tintColorLight,
    icon: '#64748b', // muted-foreground
    tabIconDefault: '#64748b',
    tabIconSelected: tintColorLight,
    card: '#ffffff',
    border: '#e2e8f0',
    muted: '#f1f5f9',
    mutedForeground: '#64748b',
    placeholder: '#94a3b8', // Tailwind slate-400 equivalent for good contrast
    // Status colors
    error: '#ef4444', // red-500
    warning: '#f59e0b', // amber-500
    success: '#10b981', // emerald-500
  },
  dark: {
    text: '#f8fafc', // foreground
    background: '#0f172a',
    tint: tintColorDark,
    icon: '#94a3b8', // muted-foreground
    tabIconDefault: '#94a3b8',
    tabIconSelected: tintColorDark,
    card: '#1e293b',
    border: '#1e293b',
    muted: '#1e293b',
    mutedForeground: '#94a3b8',
    placeholder: '#475569', // Tailwind slate-600 equivalent
    // Status colors
    error: '#ef4444', // red-500
    warning: '#f59e0b', // amber-500
    success: '#10b981', // emerald-500
  },
};

export const Fonts = Platform.select({
  ios: {
    /** iOS `UIFontDescriptorSystemDesignDefault` */
    sans: 'system-ui',
    /** iOS `UIFontDescriptorSystemDesignSerif` */
    serif: 'ui-serif',
    /** iOS `UIFontDescriptorSystemDesignRounded` */
    rounded: 'ui-rounded',
    /** iOS `UIFontDescriptorSystemDesignMonospaced` */
    mono: 'ui-monospace',
  },
  default: {
    sans: 'normal',
    serif: 'serif',
    rounded: 'normal',
    mono: 'monospace',
  },
  web: {
    sans: "system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
    serif: "Georgia, 'Times New Roman', serif",
    rounded: "'SF Pro Rounded', 'Hiragino Maru Gothic ProN', Meiryo, 'MS PGothic', sans-serif",
    mono: "SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace",
  },
});
