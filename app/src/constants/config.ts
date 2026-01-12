// src/constants/config.ts
import Constants from 'expo-constants';
import { Platform } from 'react-native';

const localhost = Platform.OS === 'ios' ? 'localhost:8000' : '10.0.2.2:8000';

const getApiUrl = () => {
    if (process.env.EXPO_PUBLIC_API_URL) {
        return process.env.EXPO_PUBLIC_API_URL;
    }

    const debuggerHost = Constants.expoConfig?.hostUri;
    if (debuggerHost) {
        return `http://${debuggerHost.split(':')[0]}:8000`;
    }

    return `http://${localhost}`;
}

export const CONFIG = {
  API_URL: getApiUrl(),
};
