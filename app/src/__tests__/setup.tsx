/**
 * Global test setup for component and hook tests.
 * Mocks native modules that are not available in the test environment.
 *
 * Note: We do NOT use jest-expo preset because it's incompatible with Jest 30
 * (Expo's winter runtime triggers "import outside scope" errors).
 * Instead we configure babel-jest + babel-preset-expo manually.
 */

// --- React Native globals (normally set by react-native/jest/setup.js) ---
(globalThis as any).__DEV__ = true;
(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;
(globalThis as any).IS_REACT_NATIVE_TEST_ENVIRONMENT = true;
(globalThis as any).window = globalThis;
(globalThis as any).requestAnimationFrame = (cb: (t: number) => void) => setTimeout(() => cb(Date.now()), 0);
(globalThis as any).cancelAnimationFrame = (id: number) => clearTimeout(id);

// --- expo (prevent winter runtime from loading) ---
jest.mock('expo', () => ({}));


// --- expo-secure-store ---
jest.mock('expo-secure-store', () => {
  const store: Record<string, string> = {};
  return {
    setItemAsync: jest.fn(async (key: string, value: string) => { store[key] = value; }),
    getItemAsync: jest.fn(async (key: string) => store[key] ?? null),
    deleteItemAsync: jest.fn(async (key: string) => { delete store[key]; }),
  };
});

// --- expo-localization ---
jest.mock('expo-localization', () => ({
  getLocales: jest.fn(() => [{ languageCode: 'en', languageTag: 'en-US' }]),
}));

// --- expo-router ---
jest.mock('expo-router', () => ({
  useRouter: jest.fn(() => ({
    push: jest.fn(),
    replace: jest.fn(),
    back: jest.fn(),
    dismissAll: jest.fn(),
  })),
  useLocalSearchParams: jest.fn(() => ({})),
  useSegments: jest.fn(() => []),
  Link: 'Link',
}));

// --- expo-haptics ---
jest.mock('expo-haptics', () => ({
  impactAsync: jest.fn(),
  notificationAsync: jest.fn(),
  selectionAsync: jest.fn(),
  ImpactFeedbackStyle: { Light: 'light', Medium: 'medium', Heavy: 'heavy' },
  NotificationFeedbackType: { Success: 'success', Warning: 'warning', Error: 'error' },
}));

// --- expo-audio ---
jest.mock('expo-audio', () => ({
  useAudioRecorder: jest.fn(() => ({
    prepareToRecordAsync: jest.fn(),
    record: jest.fn(),
    stop: jest.fn(),
    uri: null,
  })),
  AudioModule: {
    getRecordingPermissionsAsync: jest.fn(async () => ({ granted: true })),
    requestRecordingPermissionsAsync: jest.fn(async () => ({ granted: true })),
    setAudioModeAsync: jest.fn(),
  },
  RecordingPresets: {
    HIGH_QUALITY: {},
  },
}));

// --- expo-image-picker ---
jest.mock('expo-image-picker', () => ({
  launchImageLibraryAsync: jest.fn(),
  launchCameraAsync: jest.fn(),
  requestMediaLibraryPermissionsAsync: jest.fn(async () => ({ status: 'granted' })),
  requestCameraPermissionsAsync: jest.fn(async () => ({ status: 'granted' })),
  PermissionStatus: { GRANTED: 'granted', DENIED: 'denied', UNDETERMINED: 'undetermined' },
}));

// --- expo-camera ---
jest.mock('expo-camera', () => ({
  Camera: 'Camera',
  useCameraPermissions: jest.fn(() => [{ granted: false }, jest.fn()]),
}));

// --- nativewind ---
jest.mock('nativewind', () => ({
  useColorScheme: jest.fn(() => ({
    colorScheme: 'light',
    setColorScheme: jest.fn(),
    toggleColorScheme: jest.fn(),
  })),
  styled: (component: any) => component,
}));

// --- react-native-css-interop (used internally by nativewind) ---
jest.mock('react-native-css-interop', () => ({
  cssInterop: jest.fn((component: any) => component),
  remapProps: jest.fn(),
}));

// --- @react-native-google-signin/google-signin ---
jest.mock('@react-native-google-signin/google-signin', () => ({
  GoogleSignin: {
    configure: jest.fn(),
    hasPlayServices: jest.fn(async () => true),
    signIn: jest.fn(async () => ({ data: { idToken: 'mock-id-token' } })),
    signOut: jest.fn(),
  },
  statusCodes: {
    SIGN_IN_CANCELLED: 'SIGN_IN_CANCELLED',
    IN_PROGRESS: 'IN_PROGRESS',
    PLAY_SERVICES_NOT_AVAILABLE: 'PLAY_SERVICES_NOT_AVAILABLE',
  },
}));

// --- react-native-gesture-handler ---
jest.mock('react-native-gesture-handler', () => ({
  Swipeable: 'Swipeable',
  GestureHandlerRootView: ({ children }: any) => children,
  PanGestureHandler: 'PanGestureHandler',
}));

// --- expo-constants ---
jest.mock('expo-constants', () => ({
  __esModule: true,
  default: {
    expoConfig: { hostUri: 'localhost:8081' },
  },
}));

// --- react-native-reanimated (manual mock — react-native-reanimated/mock imports worklets ESM) ---
jest.mock('react-native-reanimated', () => ({
  __esModule: true,
  default: {
    call: jest.fn(),
    createAnimatedComponent: (c: any) => c,
    addWhitelistedNativeProps: jest.fn(),
    addWhitelistedUIProps: jest.fn(),
  },
  useSharedValue: jest.fn((v: any) => ({ value: v })),
  useAnimatedStyle: jest.fn((f: () => any) => f()),
  useAnimatedProps: jest.fn(() => ({ animatedProps: {} })),
  useDerivedValue: jest.fn((f: () => any) => ({ value: f() })),
  withTiming: jest.fn((v: any) => v),
  withSpring: jest.fn((v: any) => v),
  withDecay: jest.fn((v: any) => v),
  withDelay: jest.fn((_d: any, v: any) => v),
  withSequence: jest.fn((...args: any[]) => args[args.length - 1]),
  withRepeat: jest.fn((a: any) => a),
  cancelAnimation: jest.fn(),
  Easing: { linear: jest.fn(), ease: jest.fn(), bezier: jest.fn(() => jest.fn()) },
  FadeIn: { duration: jest.fn().mockReturnThis() },
  FadeOut: { duration: jest.fn().mockReturnThis() },
  Layout: { duration: jest.fn().mockReturnThis(), springify: jest.fn().mockReturnThis() },
  SlideInRight: {},
  SlideOutLeft: {},
  createAnimatedComponent: (c: any) => c,
  Animated: {
    View: 'Animated.View',
    Text: 'Animated.Text',
    Image: 'Animated.Image',
    ScrollView: 'Animated.ScrollView',
    createAnimatedComponent: (c: any) => c,
  },
}));

// --- expo-linear-gradient ---
jest.mock('expo-linear-gradient', () => ({
  LinearGradient: 'LinearGradient',
}));

// --- react-native-svg (for CircularProgress, NutrientRing) ---
jest.mock('react-native-svg', () => ({
  __esModule: true,
  default: 'Svg',
  Svg: 'Svg',
  Circle: 'Circle',
  Rect: 'Rect',
  Path: 'Path',
  G: 'G',
  Text: 'SvgText',
  Line: 'Line',
}));

// --- react-native-gesture-handler/ReanimatedSwipeable (FoodEntryItem) ---
jest.mock('react-native-gesture-handler/ReanimatedSwipeable', () => {
  return {
    __esModule: true,
    default: ({ children }: any) => children,
  };
});

// --- react-native-safe-area-context (SettingsModal, screens) ---
jest.mock('react-native-safe-area-context', () => ({
  useSafeAreaInsets: jest.fn(() => ({ top: 0, bottom: 0, left: 0, right: 0 })),
  SafeAreaView: 'SafeAreaView',
  SafeAreaProvider: ({ children }: any) => children,
}));

// Suppress console.warn/error noise in tests (patched directly — setupFiles runs before Jest globals)
const originalWarn = console.warn;
const originalError = console.error;
console.warn = (...args: any[]) => {
  if (typeof args[0] === 'string' && args[0].includes('Reanimated')) return;
  originalWarn(...args);
};
console.error = (...args: any[]) => {
  if (typeof args[0] === 'string' && args[0].includes('act(')) return;
  originalError(...args);
};
