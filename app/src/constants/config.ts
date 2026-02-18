import Constants from 'expo-constants';
import { Platform } from 'react-native';

const localhost = Platform.OS === 'ios' ? 'localhost:8000' : '10.0.2.2:8000';

const getApiUrl = () => {
    const debuggerHost = Constants.expoConfig?.hostUri;
    const isAndroidEmulator = Platform.OS === 'android' && !debuggerHost?.includes('192.168');

    if (process.env.EXPO_PUBLIC_API_URL) {
        // If we are on Android emulator and the env var is a local network IP, swap it to 10.0.2.2
        if (isAndroidEmulator && process.env.EXPO_PUBLIC_API_URL.includes('192.168')) {
            return process.env.EXPO_PUBLIC_API_URL.replace(/192\.168\.\d+\.\d+/, '10.0.2.2');
        }
        return process.env.EXPO_PUBLIC_API_URL;
    }

    if (debuggerHost) {
        return `http://${debuggerHost.split(':')[0]}:8000`;
    }

    return `http://${localhost}`;
}

export const CONFIG = {
  API_URL: getApiUrl(),
};
