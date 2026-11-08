import * as Notifications from 'expo-notifications';
import { useRouter } from 'expo-router';
import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { AppState, AppStateStatus } from 'react-native';

import { api } from './api';
import { useAuth } from './auth';
import {
  presentLocalNotification,
  registerPushToken,
  setAppBadge,
  setupNotificationChannel,
} from './notifications';
import { AppNotification } from './types';

const POLL_INTERVAL_MS = 20000;

interface LiveNotificationsState {
  unreadCount: number;
  latest: AppNotification[];
  refresh: () => Promise<void>;
  markRead: (ids?: number[]) => Promise<void>;
}

const LiveNotificationsContext = createContext<LiveNotificationsState | null>(null);

export function LiveNotificationsProvider({ children }: { children: React.ReactNode }) {
  const { token } = useAuth();
  const router = useRouter();
  const [unreadCount, setUnreadCount] = useState(0);
  const [latest, setLatest] = useState<AppNotification[]>([]);

  const latestId = useRef<number | null>(null);
  const polling = useRef(false);
  const appState = useRef<AppStateStatus>(AppState.currentState);
  const handledResponse = useRef<string | null>(null);
  const recentlyReceived = useRef<Map<string, number>>(new Map());

  const showLiveUpdate = useCallback((title: string, body: string, data: Record<string, unknown>) => {
    // If the same update already arrived as a push notification, don't show it twice.
    const key = `${title.slice(0, 120)}|${body.slice(0, 180)}`;
    const seenAt = recentlyReceived.current.get(key);
    if (seenAt && Date.now() - seenAt < 120000) return;
    presentLocalNotification(title, body, data);
  }, []);

  const applyUnread = useCallback((count: number) => {
    setUnreadCount(count);
  }, []);

  useEffect(() => {
    setAppBadge(unreadCount);
  }, [unreadCount]);

  const fetchLatest = useCallback(
    async (live: boolean) => {
      if (!token || polling.current) return;
      polling.current = true;
      try {
        const since = live ? latestId.current : null;
        const res = await api.notifications(token, since ?? undefined);

        if (since != null && res.results.length > 0) {
          const fresh = res.results;
          setLatest((prev) => [...fresh].reverse().concat(prev).slice(0, 100));

          const newest = fresh[fresh.length - 1];
          if (fresh.length === 1) {
            showLiveUpdate(newest.title, newest.message, { kind: newest.kind, url: newest.url });
          } else {
            showLiveUpdate(
              `${fresh.length} new updates from FBMI`,
              newest.message || 'Tap to see what has been posted.',
              { kind: newest.kind, url: '/notifications' },
            );
          }
        } else if (since == null) {
          setLatest(res.results);
        }

        latestId.current = Math.max(latestId.current ?? 0, res.latest_id || 0);
        applyUnread(res.unread_count);
      } catch {
        // offline or server asleep: keep the last known badge
      } finally {
        polling.current = false;
      }
    },
    [token, applyUnread, showLiveUpdate],
  );

  const refresh = useCallback(async () => {
    await fetchLatest(false);
  }, [fetchLatest]);

  const markRead = useCallback(
    async (ids?: number[]) => {
      if (!token) return;
      setUnreadCount((count) => (ids && ids.length ? Math.max(0, count - ids.length) : 0));
      try {
        const res = await api.markNotificationsRead(token, ids);
        applyUnread(res.unread_count);
      } catch {
        // keep optimistic value; the next poll corrects it
      }
    },
    [token, applyUnread],
  );

  // Register the device for push notifications whenever the session changes.
  useEffect(() => {
    if (!token) return;
    (async () => {
      await setupNotificationChannel();
      await registerPushToken(token);
      await fetchLatest(false);
    })();
  }, [token, fetchLatest]);

  // Poll while the app is open, and immediately when it returns to the foreground.
  useEffect(() => {
    if (!token) return;
    const timer = setInterval(() => {
      if (appState.current === 'active') fetchLatest(true);
    }, POLL_INTERVAL_MS);

    const sub = AppState.addEventListener('change', (state) => {
      appState.current = state;
      if (state === 'active') {
        registerPushToken(token);
        fetchLatest(true);
      }
    });

    return () => {
      clearInterval(timer);
      sub.remove();
    };
  }, [token, fetchLatest]);

  // Remember pushes we just showed so live polling doesn't double-alert.
  useEffect(() => {
    const sub = Notifications.addNotificationReceivedListener((notification) => {
      const { title, body } = notification.request.content;
      recentlyReceived.current.set(
        `${(title ?? '').slice(0, 120)}|${(body ?? '').slice(0, 180)}`,
        Date.now(),
      );
    });
    return () => sub.remove();
  }, []);

  // Open the relevant screen when a notification is tapped.
  useEffect(() => {
    if (!token) return;

    function open(notification: Notifications.Notification | undefined) {
      if (!notification) return;
      const id = notification.request.identifier;
      if (handledResponse.current === id) return;
      handledResponse.current = id;
      const url = notification.request.content.data?.url;
      router.push((typeof url === 'string' && url.startsWith('/') ? url : '/notifications') as never);
    }

    const last = Notifications.getLastNotificationResponse();
    if (last?.notification) {
      open(last.notification);
      Notifications.clearLastNotificationResponseAsync?.().catch(() => undefined);
    }

    const sub = Notifications.addNotificationResponseReceivedListener((response) => {
      open(response.notification);
    });
    return () => sub.remove();
  }, [router, token]);

  const value = useMemo(
    () => ({ unreadCount, latest, refresh, markRead }),
    [unreadCount, latest, refresh, markRead],
  );

  return <LiveNotificationsContext.Provider value={value}>{children}</LiveNotificationsContext.Provider>;
}

export function useLiveNotifications(): LiveNotificationsState {
  const ctx = useContext(LiveNotificationsContext);
  if (!ctx) throw new Error('useLiveNotifications must be used within LiveNotificationsProvider');
  return ctx;
}
