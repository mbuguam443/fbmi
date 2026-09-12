import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import { Pressable, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card } from '../../components/ui';
import { MODULES } from '../../lib/library';
import { Colors, Radius, Spacing } from '../../lib/theme';

export default function LibraryScreen() {
  const router = useRouter();
  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <View style={styles.content}>
        <Text style={styles.title}>Library</Text>
        <Text style={styles.subtitle}>Browse your personal church records</Text>
        <Card style={styles.padCard}>
          {MODULES.map((m, i) => (
            <View key={m.kind}>
              {i > 0 && <View style={styles.divider} />}
              <Pressable
                onPress={() => router.push({ pathname: '/list/[kind]', params: { kind: m.kind } })}
                style={({ pressed }) => [styles.rowPressable, pressed && styles.pressed]}>
                <View style={styles.iconBox}>
                  <Ionicons name={m.icon as keyof typeof Ionicons.glyphMap} size={20} color={Colors.navy} />
                </View>
                <View style={styles.rowText}>
                  <Text style={styles.rowTitle}>{m.title}</Text>
                  <Text style={styles.rowSubtitle}>{m.subtitle}</Text>
                </View>
                <Ionicons name="chevron-forward" size={18} color={Colors.muted} />
              </Pressable>
            </View>
          ))}
        </Card>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.lg, gap: Spacing.md },
  title: { fontSize: 28, fontWeight: '900', color: Colors.navy },
  subtitle: { fontSize: 14, color: Colors.muted, marginTop: -Spacing.sm },
  padCard: { paddingHorizontal: Spacing.md },
  divider: { height: StyleSheet.hairlineWidth, backgroundColor: Colors.border, marginVertical: Spacing.sm },
  pressed: { opacity: 0.6 },
  rowPressable: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, paddingVertical: Spacing.sm + 2 },
  iconBox: {
    width: 40,
    height: 40,
    borderRadius: Radius.sm,
    backgroundColor: Colors.bg,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowText: { flex: 1 },
  rowTitle: { fontSize: 15, fontWeight: '700', color: Colors.text },
  rowSubtitle: { fontSize: 13, color: Colors.muted, marginTop: 1 },
});