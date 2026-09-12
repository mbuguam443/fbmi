import { Ionicons } from '@expo/vector-icons';
import { Stack, useFocusEffect, useLocalSearchParams } from 'expo-router';
import { useCallback, useState } from 'react';
import { Linking, ScrollView, StyleSheet, Text, View } from 'react-native';

import { Btn, Chip, Loading } from '../../../components/ui';
import { useAuth } from '../../../lib/auth';
import { api } from '../../../lib/api';
import { moduleTitle } from '../../../lib/library';
import { Colors, formatDate, Radius, Spacing } from '../../../lib/theme';

export default function ReadScreen() {
  const { kind, id } = useLocalSearchParams<{ kind: string; id: string }>();
  const { token } = useAuth();
  const [item, setItem] = useState<Record<string, any> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!token || !id) return;
    try {
      const endpoint = kind === 'bible-study' ? `bible-study/${id}/` : kind === 'songs' ? `songs/${id}/` : `sermons/${id}/`;
      setItem(await api.detail<Record<string, any>>(token, endpoint));
      setError(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Could not load the note.');
    }
  }, [token, kind, id]);

  useFocusEffect(
    useCallback(() => {
      load();
    }, [load]),
  );

  const title = item?.title ? String(item.title) : moduleTitle(kind);

  return (
    <View style={styles.safe}>
      <Stack.Screen options={{ title: moduleTitle(kind) }} />
      {error ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{error}</Text>
        </View>
      ) : !item ? (
        <Loading />
      ) : (
        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.metaRow}>
            {kind === 'sermons' && item.category ? <Chip label={String(item.category)} /> : null}
            {kind === 'songs' && item.category_label ? <Chip label={String(item.category_label)} /> : null}
            {item.date ? <Chip label={formatDate(item.date)} bg="#EEECE5" color={Colors.muted} /> : null}
            {item.study_date ? <Chip label={formatDate(item.study_date)} bg="#EEECE5" color={Colors.muted} /> : null}
            {item.bible_verse ? <Chip label={`${item.bible_verse}`} bg={Colors.navySoft} color={Colors.navy} /> : null}
            {item.scripture ? <Chip label={`${item.scripture}`} bg={Colors.navySoft} color={Colors.navy} /> : null}
          </View>

          <Text style={styles.title}>{title}</Text>

          {item.speaker ? <Text style={styles.subtitle}>By {item.speaker}</Text> : null}
          {item.teacher ? <Text style={styles.subtitle}>Taught by {item.teacher}</Text> : null}
          {item.author ? <Text style={styles.subtitle}>{item.author}</Text> : null}
          {item.key || item.tempo ? (
            <Text style={styles.subtitle}>
              {(item.key ? `Key ${item.key}` : '')}
              {item.key && item.tempo ? ' · ' : ''}
              {item.tempo ? item.tempo : ''}
            </Text>
          ) : null}

          {kind === 'songs' ? (
            <View style={styles.lyricsBox}>
              {String(item.lyrics || '')
                .split('\n')
                .map((line, i) => (
                  <Text key={i} style={[styles.lyricsLine, line.trim() === '' && styles.lyricsSpacer]}>
                    {line}
                  </Text>
                ))}
            </View>
          ) : (
            <>
              {item.description ? <Section label="About this message" body={String(item.description)} /> : null}
              {kind === 'bible-study' ? (
                <>
                  {item.content ? <Section label="Study notes" body={String(item.content)} /> : null}
                  {item.key_points ? <Section label="Key points" body={String(item.key_points)} /> : null}
                  {item.prayer_points ? <Section label="Prayer points" body={String(item.prayer_points)} /> : null}
                  {item.discussion_questions ? (
                    <Section label="Discussion questions" body={String(item.discussion_questions)} />
                  ) : null}
                </>
              ) : (
                <>
                  {item.sermon_notes ? <Section label="Sermon notes" body={String(item.sermon_notes)} /> : null}
                  {!item.sermon_notes && !item.description ? (
                    <Text style={styles.emptyText}>No notes published for this message yet.</Text>
                  ) : null}
                </>
              )}
            </>
          )}

          {item.youtube_url ? (
            <Btn
              title="Watch on YouTube"
              style={styles.actionBtn}
              onPress={() => Linking.openURL(String(item.youtube_url))}
            />
          ) : null}
          {item.pdf_url ? (
            <Btn
              title="Open study PDF"
              variant="outline"
              style={styles.actionBtn}
              onPress={() => Linking.openURL(String(item.pdf_url))}
            />
          ) : null}
        </ScrollView>
      )}
    </View>
  );
}

function Section({ label, body }: { label: string; body: string }) {
  return (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Ionicons name="bookmark" size={14} color={Colors.gold} />
        <Text style={styles.sectionLabel}>{label}</Text>
      </View>
      <Text style={styles.sectionBody}>{body}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: Colors.bg },
  center: { flex: 1, alignItems: 'center', justifyContent: 'center', padding: Spacing.xl },
  errorText: { color: Colors.danger, fontSize: 14, textAlign: 'center' },
  emptyText: { color: Colors.muted, fontSize: 14 },
  content: { padding: Spacing.lg, paddingBottom: Spacing.xl, gap: Spacing.md },
  metaRow: { flexDirection: 'row', flexWrap: 'wrap', gap: Spacing.sm },
  title: { fontSize: 22, fontWeight: '900', color: Colors.text, marginTop: Spacing.xs },
  subtitle: { fontSize: 14, color: Colors.muted, fontWeight: '600' },
  lyricsBox: {
    backgroundColor: Colors.card,
    borderRadius: Radius.lg,
    borderWidth: 1,
    borderColor: Colors.border,
    padding: Spacing.lg,
  },
  lyricsLine: { fontSize: 15, lineHeight: 26, color: Colors.text },
  lyricsSpacer: { height: Spacing.sm },
  section: { backgroundColor: Colors.card, borderRadius: Radius.lg, padding: Spacing.lg, gap: Spacing.sm },
  sectionHeader: { flexDirection: 'row', alignItems: 'center', gap: Spacing.xs },
  sectionLabel: { fontSize: 12, fontWeight: '800', color: Colors.text, textTransform: 'uppercase', letterSpacing: 0.4 },
  sectionBody: { fontSize: 15, lineHeight: 25, color: Colors.text },
  actionBtn: { marginTop: Spacing.xs },
});