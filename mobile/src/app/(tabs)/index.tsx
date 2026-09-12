import { Ionicons } from '@expo/vector-icons';
import { useFocusEffect, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { Pressable, RefreshControl, ScrollView, StyleSheet, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Card, Chip, EmptyState, Loading, SectionTitle } from '../../components/ui';
import { useAuth } from '../../lib/auth';
import { api } from '../../lib/api';
import { MODULES } from '../../lib/library';
import { Colors, formatDate, formatMoney, initials, Radius, Spacing } from '../../lib/theme';
import { Announcement, ChurchEvent, PortalData } from '../../lib/types';

export default function PortalScreen() {
  const { token, user, member, refresh } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<PortalData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);

  const load = useCallback(async () => {
    if (!token) return;
    try {
      setData(await api.portal(token));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load portal.');
    }
  }, [token]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await Promise.all([load(), refresh()]);
    setRefreshing(false);
  }, [load, refresh]);

  return (
    <SafeAreaView style={styles.safe} edges={['top']}>
      <ScrollView
        contentContainerStyle={styles.content}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.navy} />}>
        <View style={styles.hero}>
          <View style={styles.heroTopRow}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>{initials(user?.full_name)}</Text>
            </View>
            <View style={styles.heroText}>
              <Text style={styles.greeting}>Shalom,</Text>
              <Text style={styles.name}>{user?.full_name || 'Member'}</Text>
              <Text style={styles.subline}>
                {member ? `${member.member_number} · ${member.membership_status_label}` : user?.role_label}
              </Text>
            </View>
          </View>
          <View style={styles.goldBar} />
        </View>

        {error && !data && <EmptyState icon="cloud-offline-outline" text={error} />}

        {data ? (
          <>
            <View style={styles.grid}>
              <StatTile
                icon="people-outline"
                label="Groups"
                value={data.counts.groups}
                onPress={() => router.push({ pathname: '/list/[kind]', params: { kind: 'groups' } })}
              />
              <StatTile
                icon="wallet-outline"
                label="Giving"
                value={formatMoney(data.counts.givings_total)}
                onPress={() => router.push({ pathname: '/list/[kind]', params: { kind: 'givings' } })}
              />
              <StatTile
                icon="calendar-outline"
                label="Attendance"
                value={data.counts.attendance}
                onPress={() => router.push({ pathname: '/list/[kind]', params: { kind: 'attendance' } })}
              />
              <StatTile
                icon="megaphone-outline"
                label="Events"
                value={data.counts.events}
                onPress={() => router.push({ pathname: '/list/[kind]', params: { kind: 'events' } })}
              />
            </View>

            <SectionTitle>Quick access</SectionTitle>
            <Card style={styles.padCard}>
              {MODULES.map((m, i) => (
                <View key={m.kind}>
                  {i > 0 && <View style={styles.divider} />}
                  <Pressable
                    onPress={() => router.push({ pathname: '/list/[kind]', params: { kind: m.kind } })}
                    style={({ pressed }) => [styles.rowPressable, pressed && styles.pressed]}>
                    <View style={styles.iconBox}>
                      <Ionicons name={m.icon as keyof typeof Ionicons.glyphMap} size={18} color={Colors.navy} />
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

            <UpcomingEvents events={data.events} />
            <Announcements items={data.announcements} />
          </>
        ) : !error ? (
          <Loading />
        ) : null}
      </ScrollView>
    </SafeAreaView>
  );
}

function StatTile({
  icon,
  label,
  value,
  onPress,
}: {
  icon: string;
  label: string;
  value: string | number;
  onPress: () => void;
}) {
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [styles.tileWrap, pressed && styles.pressed]}>
      <Card style={styles.tile}>
        <View style={styles.tileIcon}>
          <Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={18} color={Colors.navy} />
        </View>
        <Text style={styles.tileValue} numberOfLines={1} adjustsFontSizeToFit>
          {value}
        </Text>
        <Text style={styles.tileLabel}>{label}</Text>
      </Card>
    </Pressable>
  );
}

function UpcomingEvents({ events }: { events: ChurchEvent[] }) {
  if (events.length === 0) return null;
  return (
    <>
      <SectionTitle>Upcoming events</SectionTitle>
      <Card>
        {events.map((e, i) => (
          <View key={e.id}>
            {i > 0 && <View style={styles.divider} />}
            <View style={styles.eventRow}>
              <View style={styles.dateBadge}>
                <Text style={styles.dateDay}>{new Date(e.date).getDate()}</Text>
                <Text style={styles.dateMonth}>
                  {new Date(e.date).toLocaleString('en-KE', { month: 'short' })}
                </Text>
              </View>
              <View style={styles.rowText}>
                <Text style={styles.rowTitle}>{e.name}</Text>
                <Text style={styles.rowSubtitle}>{e.location || 'FBMI'} · {formatDate(e.date)}</Text>
              </View>
              <Chip label={e.registered ? 'Registered' : 'Open'} />
            </View>
          </View>
        ))}
      </Card>
    </>
  );
}

function Announcements({ items }: { items: Announcement[] }) {
  if (items.length === 0) return null;
  return (
    <>
      <SectionTitle>Announcements</SectionTitle>
      <Card>
        {items.map((a, i) => (
          <View key={a.id}>
            {i > 0 && <View style={styles.divider} />}
            <Text style={styles.rowTitle}>{a.title}</Text>
            <Text style={styles.rowSubtitle} numberOfLines={2}>
              {a.message}
            </Text>
            <Text style={styles.dateLine}>{formatDate(a.publish_date)}</Text>
          </View>
        ))}
      </Card>
    </>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.lg, paddingBottom: Spacing.xl, gap: Spacing.lg },
  hero: {
    backgroundColor: Colors.navy,
    borderRadius: Radius.lg,
    padding: Spacing.lg,
  },
  heroTopRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md },
  avatar: {
    width: 54,
    height: 54,
    borderRadius: 27,
    backgroundColor: 'rgba(255,255,255,0.18)',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.35)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarText: { color: '#FFF', fontSize: 20, fontWeight: '800' },
  heroText: { flex: 1, gap: 1 },
  greeting: { fontSize: 13, color: 'rgba(255,255,255,0.85)', fontWeight: '700' },
  name: { fontSize: 22, fontWeight: '900', color: '#FFFFFF' },
  subline: { fontSize: 12, color: 'rgba(255,255,255,0.8)', marginTop: 2 },
  goldBar: {
    marginTop: Spacing.md,
    height: 3,
    width: 64,
    borderRadius: 999,
    backgroundColor: Colors.gold,
  },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  tileWrap: { width: '48%', flexGrow: 1 },
  tile: { gap: Spacing.xs, minHeight: 96 },
  tileIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: Colors.navySoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  tileValue: { fontSize: 16, fontWeight: '900', color: Colors.navy, marginTop: Spacing.xs },
  tileLabel: { fontSize: 12, color: Colors.muted, fontWeight: '600' },
  padCard: { paddingHorizontal: Spacing.md },
  divider: { height: StyleSheet.hairlineWidth, backgroundColor: Colors.border, marginVertical: Spacing.sm },
  pressed: { opacity: 0.6 },
  rowPressable: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, paddingVertical: Spacing.sm },
  iconBox: {
    width: 38,
    height: 38,
    borderRadius: Radius.sm,
    backgroundColor: Colors.navySoft,
    alignItems: 'center',
    justifyContent: 'center',
  },
  rowText: { flex: 1 },
  rowTitle: { fontSize: 15, fontWeight: '700', color: Colors.text },
  rowSubtitle: { fontSize: 13, color: Colors.muted, marginTop: 1 },
  eventRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.md, paddingVertical: Spacing.sm },
  dateBadge: {
    width: 44,
    height: 44,
    borderRadius: Radius.sm,
    backgroundColor: Colors.goldLight,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dateDay: { fontSize: 16, fontWeight: '900', color: Colors.navy },
  dateMonth: { fontSize: 10, fontWeight: '700', color: Colors.muted, textTransform: 'capitalize' },
  dateLine: { fontSize: 12, color: Colors.muted, marginTop: Spacing.xs },
});