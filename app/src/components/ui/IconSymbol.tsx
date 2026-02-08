import React from 'react';
import { StyleProp, TextStyle, OpaqueColorValue, ViewStyle } from 'react-native';
import {
  House,
  Send,
  CodeXml,
  ChevronRight,
  ChevronLeft,
  ChevronUp,
  ChevronDown,
  Calendar,
  BarChart3,
  User,
  Plus,
  Moon,
  Sun,
  Settings,
  X,
  Globe,
  Lock,
  Pencil,
  Ruler,
  Scale,
  Target,
  Activity,
  TrendingDown,
  Minus,
  TrendingUp,
  LogOut,
  Search,
  ScanBarcode,
  Mic,
  Camera,
  XCircle,
  PlusCircle,
  Flame,
  Utensils,
  BadgeCheck,
  LucideIcon,
  Trash2,
  Check,
  AlertCircle,
  Square,
  Hourglass,
  Clock,
  Sunrise,
  Coffee,
  Carrot,
  CheckCircle,
  AlertTriangle,
  Image,
} from 'lucide-react-native';

// Map SF Symbol names to Lucide Components
// Using specific Lucide components ensures tree-shaking works (if supported) 
// and gives us type safety if we wanted it.
const MAPPING: Record<string, LucideIcon> = {
  'house.fill': House,
  'paperplane.fill': Send,
  'chevron.left.forwardslash.chevron.right': CodeXml,
  'chevron.right': ChevronRight,
  'chevron.left': ChevronLeft,
  'chevron.down': ChevronDown,
  'chevron.up': ChevronUp,
  'calendar': Calendar,
  'chart.bar.fill': BarChart3,
  'person.fill': User,
  'plus': Plus,
  'moon.stars.fill': Moon,
  'sun.max.fill': Sun,
  'gear': Settings,
  'xmark': X,
  'globe': Globe,
  'lock.fill': Lock,
  'pencil': Pencil,
  'ruler': Ruler,
  'scalemass': Scale,
  'target': Target,
  'figure.run': Activity,
  'trending-down': TrendingDown,
  'minus': Minus,
  'trending-up': TrendingUp,
  'rectangle.portrait.and.arrow.right': LogOut,
  'magnifyingglass': Search,
  'barcode.viewfinder': ScanBarcode,
  'mic.fill': Mic,
  'camera.fill': Camera,
  'photo.fill': Image,
  'pencil.circle.fill': Pencil, // Approximate
  'xmark.circle.fill': XCircle,
  'plus.circle.fill': PlusCircle,
  'pencil.and.outline': Pencil, // Approximate
  'flame.fill': Flame,
  'fork.knife': Utensils,
  'checkmark.seal.fill': BadgeCheck,
  'trash.fill': Trash2,
  'checkmark': Check,
  'alert': AlertCircle,
  'stop': Square,
  'hourglass': Hourglass,
  'clock': Clock,
  'sun.horizon.fill': Sunrise,
  'cup.and.saucer.fill': Coffee,
  'carrot.fill': Carrot,
  'moon.fill': Moon,
  'trash': Trash2,
  'checkmark.circle.fill': CheckCircle,
  'exclamationmark.triangle': AlertTriangle,
  'chrome': Globe,
  'google': Globe,
};

export type IconSymbolName = keyof typeof MAPPING;

/**
 * An icon component that uses Lucide Icons on all platforms.
 */
export function IconSymbol({
  name,
  size = 24,
  color,
  style,
  fill, // Lucide icons accept fill for some, usually we use color (stroke). SF Symbols use color as fill implicitly.
  strokeWidth,
}: {
  name: IconSymbolName;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<TextStyle>; // Lucide uses ViewStyle mostly, but we can accept TextStyle to match interface
  weight?: string; // Ignored for now, Lucide uses strokeWidth
  fill?: string; // Optional fill color
  strokeWidth?: number;
}) {
  const IconComponent = MAPPING[name];

  if (!IconComponent) {
    console.warn(`IconSymbol: Icon "${name}" not found in mapping.`);
    return null;
  }

  // Handle "filled" state for SF Symbol emulation.
  // SF Symbols often have specific .fill variants. 
  // Lucide icons are strokes by default. To emulate fill, we fill the icon with the color.
  // const isFilled = name.includes('.fill');
  
  // If fill prop is provided, use it.
  // Otherwise, strictly default to 'none' to avoid SVG defaults (often black).
  // User requested to remove automatic fill for all icons, so we default to 'none'.
  const resolvedFill = fill ?? 'none';

  return (
    <IconComponent
      color={color as string}
      size={size}
      style={style as StyleProp<ViewStyle>} // Cast to ViewStyle as Lucide accepts ViewStyle
      strokeWidth={strokeWidth}
      fill={resolvedFill} 
    />
  );
}
