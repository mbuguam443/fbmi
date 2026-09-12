import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Btn, Field } from '../components/ui';
import { useAuth } from '../lib/auth';
import { Colors, Radius, Spacing } from '../lib/theme';

export default function LoginScreen() {
  const { login, serverUrl } = useAuth();
  const router = useRouter();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);

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

  return (
    <KeyboardAvoidingView
      style={styles.flex}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <ScrollView
        contentContainerStyle={styles.container}
        keyboardShouldPersistTaps="handled">
        <View style={styles.brand}>
          <View style={styles.logoCircle}>
            <Ionicons name="book" size={34} color="#FFF" />
          </View>
          <Text style={styles.brandName}>FBMI</Text>
          <Text style={styles.subtitle}>Faith Bible Ministry Church</Text>
        </View>

        {error && <Text style={styles.error}>{error}</Text>}

        <Field label="Username" value={username} onChangeText={setUsername} autoCapitalize="none" autoCorrect={false} />
        <Field
          label="Password"
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          onSubmitEditing={submit}
        />

        <Btn title={busy ? 'Signing in…' : 'Sign In'} onPress={submit} loading={busy} />

        <Pressable onPress={() => setShowAdvanced((v) => !v)} style={styles.advancedToggle}>
          <Text style={styles.advancedText}>Server settings</Text>
        </Pressable>
        {showAdvanced && (
          <View style={styles.advancedBox}>
            <Text style={styles.advancedHint}>API base URL</Text>
            <Text style={styles.serverUrl} selectable>
              {serverUrl}
            </Text>
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
  logoCircle: {
    width: 72,
    height: 72,
    borderRadius: 20,
    backgroundColor: Colors.navy,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: Spacing.sm,
  },
  brandName: {
    fontSize: 30,
    fontWeight: '900',
    color: Colors.navy,
    letterSpacing: 2,
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
  advancedToggle: {
    alignItems: 'center',
    paddingVertical: Spacing.sm,
  },
  advancedText: {
    color: Colors.info,
    fontSize: 13,
    fontWeight: '600',
  },
  advancedBox: {
    backgroundColor: Colors.card,
    borderRadius: Radius.md,
    padding: Spacing.lg,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    gap: Spacing.xs,
  },
  advancedHint: {
    fontSize: 12,
    color: Colors.muted,
    fontWeight: '600',
  },
  serverUrl: {
    fontSize: 14,
    color: Colors.text,
  },
});