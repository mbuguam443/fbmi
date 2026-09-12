import { Ionicons } from '@expo/vector-icons';
import { Stack, useFocusEffect, useLocalSearchParams, useRouter } from 'expo-router';
import { useCallback, useState } from 'react';
import { FlatList, Linking, Pressable, RefreshControl, StyleSheet, Text, View } from 'react-native';

import { Btn, Card, Chip, EmptyState, ErrorBox, Loading } from '../../components/ui';
import { useAuth } from '../../lib/auth';
import { api, ENDPOINTS } from '../../lib/api';
import { moduleTitle } from '../../lib/library';
import { Colors, formatDate, formatMoney, Spacing } from '../../lib/theme';
import {
  Announcement,
  AttendanceRecord,
  ChurchEvent,
  GivingRecord,
  Group,
  Prayer,
  Sermon,
} from '../../lib/types';

export default function ListScreen() {
  const { kind } = useLocalSearchParams<{ kind: string }>();
  const { token } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<Record<string, unknown>[] | null>(null);
  const [count, setCount] = useState(0);
  const [total, setTotal] = useState<string | undefined>(undefined);
  const [error, setError] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [busyId, setBusyId] = useState<number | null>(null);

  const endpoint = ENDPOINTS[kind] ? ENDPOINTS[kind] : 'groups/';

  const load = useCallback(async () => {
    if (!token) return;
    try {
      const res = await api.list<Record<string, unknown>>(token, endpoint);
      setData(res.results);
      setCount(res.count);
      setTotal(res.total);
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load records.');
    }
  }, [token, endpoint]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const onRefresh = useCallback(async () => {
    setRefreshing(true);
    await load();
    setRefreshing(false);
  }, [load]);

  async function toggleRegister(eventId: number) {
    if (!token) return;
    setBusyId(eventId);
    try {
      await api.registerEvent(token, eventId);
      await load();
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Registration failed.');
    } finally {
      setBusyId(null);
    }
  }

  return (
    <View style={styles.safe}>
      <Stack.Screen
        options={{
          title: moduleTitle(kind),
          headerRight:
            kind === 'prayers'
              ? () => (
                  <Pressable onPress={() => router.push('/prayers/new')} hitSlop={10}>
                    <Ionicons name="add-circle" size={26} color={Colors.navy} />
                  </Pressable>
                )
              : undefined,
        }}
      />

      {error && !data ? (
        <ErrorBox text={error} />
      ) : !data ? (
        <Loading />
      ) : (
        <FlatList
          data={data}
          keyExtractor={(_, i) => String(i)}
          contentContainerStyle={styles.content}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor={Colors.navy} />}
          ListHeaderComponent={
            count === 0 ? null : (
              <View style={styles.summary}>
                <Text style={styles.summaryText}>{count} record{count === 1 ? '' : 's'}</Text>
                {total !== undefined && <Text style={styles.summaryTotal}>{formatMoney(total)}</Text>}
              </View>
            )
          }
          ListEmptyComponent={<EmptyState icon="folder-open-outline" text="No records yet." />}
          renderItem={({ item, index }) => (
            <RowItem
              kind={kind}
              item={item}
              index={index}
              busy={busyId === (item as unknown as ChurchEvent).id}
              onRegister={() => toggleRegister((item as unknown as ChurchEvent).id)}
              onOpen={
                kind === 'sermons' && (item as unknown as Sermon).youtube_url
                  ? () => Linking.openURL((item as unknown as Sermon).youtube_url!)
                  : undefined
              }
            />
          )}
          ItemSeparatorComponent={() => <View style={styles.sep} />}
        />
      )}
    </View>
  );
}

function RowItem({
  kind,
  item,
  index,
  busy,
  onRegister,
  onOpen,
}: {
  kind: string;
  item: Record<string, any>;
  index: number;
  busy: boolean;
  onRegister: () => void;
  onOpen?: () => void;
}) {
  const row = <Card style={styles.card}>{renderBody(kind, item, index, busy, onRegister)}</Card>;
  if (!onOpen) return row;
  return (
    <Pressable onPress={onOpen} style={({ pressed }) => (pressed ? { opacity: 0.7 } : undefined)}>
      {row}
    </Pressable>
  );
}

function renderBody(kind: string, item: Record<string, any>, index: number, busy: boolean, onRegister: () => void) {
  switch (kind) {
    case 'groups': {
      const g = item as Group;
      return (
        <View style={styles.rowBody}>
          <RowLine icon="people-outline" title={g.name} />
          {g.leader ? <RowSub text={g.leader} /> : null}
          <RowSub text={`${g.meeting_day}${g.meeting_time ? ` · ${g.meeting_time}` : ''}${g.location ? ` · ${g.location}` : ''}`} />
          <Chip label={`${g.members_count} members`} />
        </View>
      );
    }
    case 'givings': {
      const it = item as GivingRecord;
      return (
        <View style={styles.rowBody}>
          <View style={styles.amountRow}>
            <Text style={styles.amount}>{formatMoney(it.amount)}</Text>
            <Chip label={it.category_label} />
          </View>
          <RowSub text={formatDate(it.date)} />
          <RowSub text={`via ${it.payment_method_label}${it.reference_number ? ` · ${it.reference_number}` : ''}`} />
        </View>
      );
    }
    case 'attendance': {
      const a = item as AttendanceRecord;
      return (
        <View style={styles.rowBody}>
          <RowLine icon="calendar-outline" title={a.service} />
          <RowSub text={formatDate(a.date)} />
          {a.location ? <RowSub text={a.location} /> : null}
        </View>
      );
    }
    case 'events': {
      const e = item as ChurchEvent;
      return (
        <View style={styles.rowBody}>
          <RowLine icon="megaphone-outline" title={e.name} />
          <RowSub text={formatDate(e.date)} />
          <RowSub text={e.location || 'FBMI'} />
          <View style={styles.eventFooter}>
            <Chip
              label={e.registration_required ? (e.registered ? 'Registered' : 'Registration open') : 'No signup needed'}
              color={e.registered ? Colors.success : e.registration_required ? Colors.navy : Colors.muted}
              bg={e.registered ? '#E5F2E6' : Colors.goldLight}
            />
            {e.registration_required && e.registered ? (
              <Btn title="Cancel" variant="outline" style={styles.smallBtn} loading={busy} onPress={onRegister} />
            ) : null}
            {e.registration_required && !e.registered ? (
              <Btn title="Register" style={styles.smallBtn} loading={busy} onPress={onRegister} />
            ) : null}
          </View>
        </View>
      );
    }
    case 'announcements': {
      const a = item as Announcement;
      return (
        <View style={styles.rowBody}>
          <RowLine icon="checkbox" title={a.title} />
          <RowSub text={a.message} />
          <RowSub text={`Published ${formatDate(a.publish_date)}${a.target_audience ? ` · ${a.target_audience}` : ''}`} />
        </View>
      );
    }
    case 'sermons': {
      const s = item as Sermon;
      return (
        <View style={styles.rowBody}>
          <RowLine icon="mic-outline" title={s.title} />
          {s.speaker ? <RowSub text={s.speaker} /> : null}
          <RowSub text={`${formatDate(s.date)}${s.bible_verse ? ` · ${s.bible_verse}` : ''}`} />
          {s.youtube_url ? (
            <View style={styles.playRow}>
              <Ionicons name="logo-youtube" size={16} color={Colors.danger} />
              <Text style={styles.playText}>Watch on YouTube</Text>
            </View>
          ) : null}
        </View>
      );
    }
    case 'prayers': {
      const p = item as Prayer;
      return (
        <View style={styles.rowBody}>
          <RowLine icon="hand-left-outline" title={p.title} />
          <RowSub text={p.request} />
          <View style={styles.eventFooter}>
            <Chip label={p.category_label} />
            <Chip label={p.status_label} color={p.status === 'answered' ? Colors.success : Colors.info} bg="#E7EDF7" />
            <Chip label={formatDate(p.date)} bg="#EEECE5" color={Colors.muted} />
          </View>
        </View>
      );
    }
    default:
      return <RowLine icon="albums-outline" title={String(item.title ?? index + 1)} />;
  }
}

function RowLine({ icon, title }: { icon: string; title: string }) {
  return (
    <View style={styles.titleRow}>
      <Ionicons name={icon as keyof typeof Ionicons.glyphMap} size={16} color={Colors.navy} />
      <Text style={styles.title}>{title}</Text>
    </View>
  );
}

function RowSub({ text }: { text: string }) {
  return <Text style={styles.sub}>{text}</Text>;
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  content: { padding: Spacing.lg, paddingBottom: Spacing.xl },
  summary: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'baseline',
    marginBottom: Spacing.sm,
    paddingHorizontal: Spacing.xs,
  },
  summaryText: { fontSize: 13, color: Colors.muted, fontWeight: '600' },
  summaryTotal: { fontSize: 15, fontWeight: '800', color: Colors.navy },
  sep: { height: Spacing.sm },
  card: { gap: Spacing.sm + 2 },
  rowBody: { gap: Spacing.xs },
  titleRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  title: { flex: 1, fontSize: 15, fontWeight: '800', color: Colors.text },
  sub: { fontSize: 13, color: Colors.muted, lineHeight: 18 },
  amountRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', gap: Spacing.sm },
  amount: { fontSize: 20, fontWeight: '900', color: Colors.navy },
  eventFooter: { flexDirection: 'row', flexWrap: 'wrap', alignItems: 'center', gap: Spacing.sm, marginTop: Spacing.xs },
  smallBtn: { height: 34, paddingHorizontal: Spacing.md },
  playRow: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xs, marginTop: Spacing.xs },
  playText: { fontSize: 13, color: Colors.danger, fontWeight: '700' },
});