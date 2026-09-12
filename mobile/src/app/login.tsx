import { useRouter } from 'expo-router';
import { useState } from 'react';
import { Image, KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Btn, Field } from '../components/ui';
import { useAuth } from '../lib/auth';
import { Colors, Radius, Spacing } from '../lib/theme';

export default function LoginScreen() {
  const { login, serverUrl, setServer } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showServer, setShowServer] = useState(false);
  const [serverEdit, setServerEdit] = useState('');
  const [savingServer, setSavingServer] = useState(false);

  async function submit() {
    if (!username.trim() || !password) {
      setError('Enter your username and password.');
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await login(username.trim(), password);
      router.replace('/(tabs)');
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Login failed.');
    } finally {
      setBusy(false);
    }
  }

  async function saveServer() {
    if (!serverEdit.trim()) return;
    setSavingServer(true);
    try {
      await setServer(serverEdit.trim().replace(/\/+$/, ''));
      setShowServer(false);
    } catch {
      setError('Could not save the server address.');
    } finally {
      setSavingServer(false);
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled">
        <View style={styles.brand}>
          <Image source={require('../../assets/images/fbmi-logo.png')} style={styles.logo} resizeMode="contain" />
          <Text style={styles.brandName}>Fruitful Brethen Ministry International</Text>
          <Text style={styles.subtitle}>Members portal</Text>
        </View>

        {error && <Text style={styles.error}>{error}</Text>}

        <Field label="Username" value={username} onChangeText={setUsername} autoCapitalize="none" autoCorrect={false} />
        <Field
          label="Password"
          value={password}
          onChangeText={setPassword}
          secure
          onSubmitEditing={submit}
        />

        <Btn title={busy ? 'Signing in…' : 'Sign In'} onPress={submit} loading={busy} />

        <Pressable onPress={() => { setServerEdit(serverUrl); setShowServer((v) => !v); }} style={styles.serverToggle}>
          <Text style={styles.serverToggleText}>API server (advanced)</Text>
        </Pressable>
        {showServer && (
          <View style={styles.serverBox}>
            <Field
              label="API base URL"
              value={serverEdit}
              onChangeText={setServerEdit}
              autoCapitalize="none"
              autoCorrect={false}
            />
            <View style={styles.serverActions}>
              <Btn title="Cancel" variant="outline" style={styles.serverBtn} onPress={() => setShowServer(false)} />
              <Btn title="Save" style={styles.serverBtn} onPress={saveServer} loading={savingServer} />
            </View>
          </View>
        )}
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1, backgroundColor: Colors.bg },
  container: {
    flexGrow: 1,
    padding: Spacing.xl,
    justifyContent: 'center',
    gap: Spacing.lg,
  },
  brand: {
    alignItems: 'center',
    gap: Spacing.xs,
    marginBottom: Spacing.xl,
  },
  logo: {
    width: 120,
    height: 120,
    marginBottom: Spacing.sm,
  },
  brandName: {
    fontSize: 20,
    fontWeight: '800',
    color: Colors.navy,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 14,
    color: Colors.muted,
  },
  error: {
    color: Colors.danger,
    fontSize: 14,
    textAlign: 'center',
  },
  serverToggle: {
    alignItems: 'center',
    paddingVertical: Spacing.sm,
  },
  serverToggleText: {
    color: Colors.info,
    fontSize: 13,
    fontWeight: '600',
  },
  serverBox: {
    backgroundColor: Colors.card,
    borderRadius: Radius.md,
    padding: Spacing.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    gap: Spacing.md,
  },
  serverActions: {
    flexDirection: 'row',
    gap: Spacing.md,
  },
  serverBtn: {
    flex: 1,
  },
});