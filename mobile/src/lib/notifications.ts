import Constants from 'expo-constants';
import * as Notifications from 'expo-notifications';
import { Platform } from 'react-native';

import { api } from './api';

export const UPDATES_CHANNEL = 'updates';

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

export async function setupNotificationChannel() {
  if (Platform.OS !== 'android') return;
  try {
    await Notifications.setNotificationChannelAsync(UPDATES_CHANNEL, {
      name: 'Church updates',
      description: 'New announcements, events, sermons and other postings',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#C9A227',
      sound: 'default',
    });
  } catch {
    // channel setup may be unavailable in some environments
  }
}

export async function requestNotificationPermission() {
  try {
    if (Platform.OS === 'android') {
      await setupNotificationChannel();
    }
    const { status } = await Notifications.getPermissionsAsync();
    if (status === 'granted') return true;
    const asked = await Notifications.requestPermissionsAsync();
    return asked.status === 'granted';
  } catch {
    return false;
  }
}

export async function registerPushToken(token: string) {
  try {
    const projectId = Constants.expoConfig?.extra?.eas?.projectId ?? Constants.easConfig?.projectId;
    if (!projectId) return false;
    const granted = await requestNotificationPermission();
    if (!granted) return false;
    const pushToken = (await Notifications.getExpoPushTokenAsync({ projectId })).data;
    await api.registerDevice(token, pushToken, Platform.OS);
    return true;
  } catch {
    // remote push requires a development/production build and push credentials
    return false;
  }
}

export async function presentLocalNotification(title: string, body: string, data: Record<string, unknown> = {}) {
  try {
    await Notifications.scheduleNotificationAsync({
      content: { title, body, sound: 'default', data },
      trigger:
        Platform.OS === 'android'
          ? {
              type: Notifications.SchedulableTriggerInputTypes.TIME_INTERVAL,
              seconds: 1,
              channelId: UPDATES_CHANNEL,
            }
          : null,
    });
  } catch {
    // notifications may be unavailable (web/simulator without permission)
  }
}

export async function setAppBadge(count: number) {
  try {
    await Notifications.setBadgeCountAsync(count);
  } catch {
    // badge support varies by launcher
  }
}
