import { Stack, useRouter, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import AsyncStorage from '@react-native-async-storage/async-storage';

import { Btn } from '../../components/ui';
import { useAuth } from '../../lib/auth';
import { api } from '../../lib/api';
import { Colors, Spacing } from '../../lib/theme';

const PENDING_KEY = 'fbmi:pendingAttend';

export default function AttendScreen() {
  const { token: qrToken } = useLocalSearchParams<{ token: string }>();
  const { token: authToken } = useAuth();
  const router = useRouter();

  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'login'>('loading');
  const [message, setMessage] = useState('');
  const [serviceName, setServiceName] = useState('');
  const processed = useRef(false);

  useEffect(() => {
    if (!qrToken) {
      const t = setTimeout(() => {
        setStatus('error');
        setMessage('No QR code data found.');
      }, 0);
      return () => clearTimeout(t);
    }
    if (!authToken) {
      AsyncStorage.setItem(PENDING_KEY, String(qrToken)).catch(() => undefined);
      const t = setTimeout(() => {
        setStatus('login');
        setMessage('Please sign in to record your attendance.');
      }, 0);
      return () => clearTimeout(t);
    }
    if (processed.current) return;
    processed.current = true;

    (async () => {
      try {
        const res = await api.scanAttendance(authToken, String(qrToken));
        setStatus('success');
        setMessage(res.created ? "You're checked in!" : 'You were already checked in.');
        setServiceName(res.service?.name ?? '');
      } catch (e) {
        setStatus('error');
        setMessage(e instanceof Error ? e.message : 'Check-in failed.');
      }
    })();
  }, [authToken, qrToken]);

  return (
    <SafeAreaView style={styles.safe}>
      <Stack.Screen options={{ title: 'Attendance check-in', headerShown: true }} />
      <View style={styles.center}>
        {status === 'loading' && <ActivityIndicator size="large" color={Colors.navy} />}
        {status === 'login' && (
          <>
            <Text style={styles.title}>Sign in to check in</Text>
            <Text style={styles.sub}>{message}</Text>
            <Btn title="Go to login" onPress={() => router.replace('/login')} />
          </>
        )}
        {status === 'success' && (
          <>
            <Text style={styles.emoji}>✅</Text>
            <Text style={styles.title}>{message}</Text>
            {serviceName ? <Text style={styles.sub}>{serviceName}</Text> : null}
            <Btn title="View my attendance" onPress={() => router.replace('/(tabs)/library')} />
          </>
        )}
        {status === 'error' && (
          <>
            <Text style={styles.emoji}>⚠️</Text>
            <Text style={styles.title}>Check-in failed</Text>
            <Text style={styles.sub}>{message}</Text>
            <Btn title="Go home" onPress={() => router.replace('/(tabs)')} />
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: Spacing.xl, gap: Spacing.md },
  emoji: { fontSize: 48 },
  title: { fontSize: 20, fontWeight: '800', color: Colors.navy, textAlign: 'center' },
  sub: { fontSize: 14, color: Colors.muted, textAlign: 'center' },
});