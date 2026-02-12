/** @type {import('jest').Config} */
module.exports = {
  projects: [
    // Project 1: Pure logic tests (utils, schemas, services)
    {
      displayName: 'logic',
      preset: 'ts-jest',
      testEnvironment: 'node',
      moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/src/$1',
      },
      testMatch: ['<rootDir>/src/__tests__/unit/**/*.test.ts'],
      transform: {
        '^.+\\.tsx?$': ['ts-jest', {
          tsconfig: {
            module: 'commonjs',
            esModuleInterop: true,
            allowSyntheticDefaultImports: true,
            strict: true,
            skipLibCheck: true,
          },
        }],
      },
      moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
    },
    // Project 2: Component and hook tests (React environment)
    // Note: jest-expo is NOT used due to Jest 30 incompatibility with Expo's winter runtime.
    // We configure babel-jest manually with babel-preset-expo instead.
    {
      displayName: 'components',
      testEnvironment: 'node',
      haste: {
        defaultPlatform: 'ios',
        platforms: ['android', 'ios', 'native'],
      },
      testMatch: [
        '<rootDir>/src/__tests__/components/**/*.test.tsx',
        '<rootDir>/src/__tests__/hooks/**/*.test.tsx',
        '<rootDir>/src/__tests__/integration/**/*.test.tsx',
      ],
      moduleNameMapper: {
        '^@/(.*)$': '<rootDir>/src/$1',
      },
      transform: {
        '\\.[jt]sx?$': ['babel-jest', {
          configFile: false,
          presets: [
            ['babel-preset-expo', { jsxImportSource: 'react' }],
          ],
        }],
      },
      transformIgnorePatterns: [
        'node_modules/(?!(' +
          'expo|' +
          'expo-.*|' +
          '@expo|' +
          '@expo/.*|' +
          'react-native|' +
          '@react-native|' +
          '@react-native/.*|' +
          '@react-native-google-signin/.*|' +
          '@react-navigation/.*|' +
          '@tanstack/.*|' +
          'zustand|' +
          'date-fns|' +
          'nativewind|' +
          'clsx|' +
          'tailwind-merge|' +
          'lucide-react-native|' +
          'react-native-gesture-handler|' +
          'react-native-reanimated|' +
          'react-native-screens|' +
          'react-native-safe-area-context|' +
          'react-native-svg|' +
          'react-native-web' +
        ')/)',
      ],
      setupFiles: [
        require.resolve('react-native/jest/setup'),
        '<rootDir>/src/__tests__/setup.tsx',
      ],
      moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
    },
  ],
};
