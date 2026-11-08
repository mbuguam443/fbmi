import { useRouter } from 'expo-router';
import { CameraView, useCameraPermissions } from 'expo-camera';
import { useRef, useState } from 'react';
import { ActivityIndicator, Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Btn } from '../components/ui';
import { useAuth } from '../lib/auth';
import { api } from '../lib/api';
import { Colors, Spacing } from '../lib/theme';

function extractToken(data: string): string {
  const marker = 'attend/';
  const idx = data.indexOf(marker);
  if (idx >= 0) return data.slice(idx + marker.length).trim();
  return data.trim();
}

export default function ScanQrScreen() {
  const { token: authToken } = useAuth();
  const router = useRouter();
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [serviceName, setServiceName] = useState('');
  const processing = useRef(false);

  async function handleScan(data: string) {
    if (processing.current) return;
    processing.current = true;
    setScanned(true);
    setStatus('loading');
    const qrToken = extractToken(data);

    if (!authToken) {
      // Save pending and go to login; login screen resumes via AsyncStorage.
      const AsyncStorage = (await import('@react-native-async-storage/async-storage')).default;
      await AsyncStorage.setItem('fbmi:pendingAttend', qrToken);
      router.replace('/login');
      return;
    }

    try {
      const res = await api.scanAttendance(authToken, qrToken);
      setStatus('success');
      setMessage(res.created ? "You're checked in!" : 'You were already checked in.');
      setServiceName(res.service?.name ?? '');
    } catch (e) {
      setStatus('error');
      setMessage(e instanceof Error ? e.message : 'Check-in failed.');
    }
  }

  if (!permission) {
    return (
      <SafeAreaView style={styles.safe}>
        <ActivityIndicator size="large" color={Colors.navy} />
      </SafeAreaView>
    );
  }

  if (!permission.granted) {
    return (
      <SafeAreaView style={styles.safe}>
        <View style={styles.center}>
          <Text style={styles.title}>Camera permission needed</Text>
          <Text style={styles.sub}>We need camera access to scan the attendance QR code at church.</Text>
          <Btn title="Grant permission" onPress={requestPermission} />
          <Btn title="Go back" variant="outline" onPress={() => router.back()} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.safe}>
      <View style={styles.header}>
        <Pressable onPress={() => router.back()} hitSlop={10}>
          <Text style={styles.back}>← Back</Text>
        </Pressable>
        <Text style={styles.headerTitle}>Scan attendance QR</Text>
      </View>

      <View style={styles.cameraWrap}>
        {status === 'idle' || status === 'loading' ? (
          <CameraView
            style={StyleSheet.absoluteFill}
            facing="back"
            onBarcodeScanned={scanned ? undefined : ({ data }) => handleScan(data)}
            barcodeScannerSettings={{ barcodeTypes: ['qr'] }}
          />
        ) : null}

        {status === 'loading' && (
          <View style={styles.overlay}>
            <ActivityIndicator size="large" color="#FFF" />
            <Text style={styles.overlayText}>Checking you in…</Text>
          </View>
        )}

        {(status === 'success' || status === 'error') && (
          <View style={styles.result}>
            <Text style={styles.resultEmoji}>{status === 'success' ? '✅' : '⚠️'}</Text>
            <Text style={styles.resultTitle}>{status === 'success' ? message : 'Check-in failed'}</Text>
            {status === 'success' && serviceName ? <Text style={styles.resultSub}>{serviceName}</Text> : null}
            {status === 'error' ? <Text style={styles.resultSub}>{message}</Text> : null}
            <View style={{ gap: Spacing.sm, width: '100%' }}>
              <Btn title="Scan again" onPress={() => { setScanned(false); processing.current = false; setStatus('idle'); setMessage(''); setServiceName(''); }} />
              <Btn title="Done" variant="outline" onPress={() => router.back()} />
            </View>
          </View>
        )}
      </View>

      {status === 'idle' && (
        <Text style={styles.hint}>Point the camera at the QR code on the wall at church.</Text>
      )}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  header: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, padding: Spacing.lg },
  back: { fontSize: 16, color: Colors.navy, fontWeight: '600' },
  headerTitle: { fontSize: 18, fontWeight: '800', color: Colors.text },
  cameraWrap: { flex: 1, margin: Spacing.lg, borderRadius: 16, overflow: 'hidden', backgroundColor: '#000' },
  hint: { textAlign: 'center', color: Colors.muted, fontSize: 13, padding: Spacing.lg },
  overlay: { ...StyleSheet.absoluteFill, alignItems: 'center', justifyContent: 'center', backgroundColor: 'rgba(0,0,0,0.5)', gap: Spacing.sm },
  overlayText: { color: '#FFF', fontSize: 14, fontWeight: '600' },
  result: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: Spacing.xl, gap: Spacing.md, backgroundColor: Colors.bg },
  resultEmoji: { fontSize: 56 },
  resultTitle: { fontSize: 20, fontWeight: '800', color: Colors.navy, textAlign: 'center' },
  resultSub: { fontSize: 14, color: Colors.muted, textAlign: 'center' },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: Spacing.xl, gap: Spacing.md },
  title: { fontSize: 20, fontWeight: '800', color: Colors.navy, textAlign: 'center' },
  sub: { fontSize: 14, color: Colors.muted, textAlign: 'center' },
});