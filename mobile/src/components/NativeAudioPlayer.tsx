import { Ionicons } from '@expo/vector-icons';
import { useAudioPlayer, useAudioPlayerStatus, setAudioModeAsync } from 'expo-audio';
import { useEffect, useState } from 'react';
import { Linking, Pressable, StyleSheet, Text, View } from 'react-native';

import { Btn } from './ui';
import { Colors, Radius, Spacing } from '../lib/theme';

function fmtTime(seconds: number) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}

export default function NativeAudioPlayer({
  uri,
  title,
  byline,
}: {
  uri: string;
  title: string;
  byline: string | null;
}) {
  const player = useAudioPlayer(uri, { updateInterval: 500 });
  const status = useAudioPlayerStatus(player);
  const [barWidth, setBarWidth] = useState(0);

  useEffect(() => {
    setAudioModeAsync({
      playsInSilentMode: true,
      shouldPlayInBackground: true,
      interruptionMode: 'doNotMix',
    }).catch(() => {});
  }, []);

  useEffect(
    () => () => {
      try {
        player.pause();
        player.setActiveForLockScreen(false);
      } catch {
        // ignore cleanup errors
      }
    },
    [player],
  );

  const duration = Number.isFinite(status.duration) && status.duration > 0 ? status.duration : 0;
  const currentTime = Number.isFinite(status.currentTime) && status.currentTime > 0 ? status.currentTime : 0;
  const progress = duration ? Math.min(1, currentTime / duration) : 0;

  const togglePlay = () => {
    try {
      if (status.playing) {
        player.pause();
        player.setActiveForLockScreen(false);
      } else {
        player.setActiveForLockScreen(true, {
          title: title || 'FBMI Message',
          artist: byline || 'FBMI Members',
        });
        player.play();
      }
    } catch {
      // playback errors are shown from status.error below
    }
  };

  const seekBy = (seconds: number) => {
    const target = Math.max(0, Math.min(currentTime + seconds, duration || currentTime + seconds));
    player.seekTo(target).catch(() => {});
  };

  return (
    <View style={styles.playerCard}>
      <View style={styles.playerHead}>
        <View style={styles.playerIcon}>
          <Ionicons name="musical-notes" size={18} color="#FFF" />
        </View>
        <View style={{ flex: 1 }}>
          <Text style={styles.playerLabel}>Listen to this message</Text>
          <Text style={styles.playerTitle} numberOfLines={1}>
            {title}
          </Text>
        </View>
      </View>

      {status.error ? (
        <View style={styles.playerError}>
          <Ionicons name="alert-circle-outline" size={16} color={Colors.danger} />
          <Text style={styles.playerErrorText}>Could not play this audio. Check your connection and try again.</Text>
        </View>
      ) : null}

      <Pressable
        style={styles.progressTrack}
        onLayout={(event) => setBarWidth(event.nativeEvent.layout.width)}
        onPress={(event) => {
          if (!barWidth || !duration) return;
          const ratio = Math.max(0, Math.min(1, event.nativeEvent.locationX / barWidth));
          player.seekTo(ratio * duration).catch(() => {});
        }}>
        <View style={[styles.progressFill, { width: `${progress * 100}%` }]} />
        <View style={[styles.progressThumb, { left: `${progress * 100}%` }]} />
      </Pressable>
      <View style={styles.playerTimes}>
        <Text style={styles.playerTime}>{fmtTime(currentTime)}</Text>
        <Text style={styles.playerTime}>{duration ? fmtTime(duration) : '--:--'}</Text>
      </View>

      <View style={styles.playerControls}>
        <Pressable style={styles.skipBtn} onPress={() => seekBy(-10)}>
          <Ionicons name="refresh-outline" size={22} color={Colors.navy} />
          <Text style={styles.skipText}>10s</Text>
        </Pressable>
        <Pressable style={styles.playBtn} onPress={togglePlay}>
          <Ionicons name={status.playing ? 'pause' : 'play'} size={26} color="#FFF" />
        </Pressable>
        <Pressable style={styles.skipBtn} onPress={() => seekBy(10)}>
          <Ionicons name="refresh" size={22} color={Colors.navy} />
          <Text style={styles.skipText}>10s</Text>
        </Pressable>
      </View>

      {status.isBuffering && !status.playing ? (
        <Text style={styles.playerHint}>Loading audio...</Text>
      ) : null}
      <Btn
        title="Open audio in browser"
        variant="outline"
        style={styles.browserBtn}
        onPress={() => Linking.openURL(uri).catch(() => {})}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  playerCard: {
    backgroundColor: Colors.card,
    borderRadius: Radius.lg,
    padding: Spacing.lg,
    gap: Spacing.sm,
    borderWidth: StyleSheet.hairlineWidth,
    borderColor: Colors.border,
    borderLeftWidth: 4,
    borderLeftColor: Colors.gold,
  },
  playerHead: { flexDirection: 'row', alignItems: 'center', gap: Spacing.sm },
  playerIcon: {
    width: 34,
    height: 34,
    borderRadius: 10,
    backgroundColor: Colors.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playerLabel: { fontSize: 11, fontWeight: '800', color: Colors.muted, textTransform: 'uppercase', letterSpacing: 0.4 },
  playerTitle: { fontSize: 15, fontWeight: '800', color: Colors.text, marginTop: 2 },
  playerError: { flexDirection: 'row', alignItems: 'center', gap: 6, marginTop: Spacing.sm },
  playerErrorText: { flex: 1, color: Colors.danger, fontSize: 12 },
  progressTrack: { height: 6, borderRadius: 999, backgroundColor: Colors.navySoft, marginTop: Spacing.md, justifyContent: 'center' },
  progressFill: { height: 6, borderRadius: 999, backgroundColor: Colors.gold },
  progressThumb: {
    position: 'absolute',
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.navy,
    marginLeft: -6,
  },
  playerTimes: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 6 },
  playerTime: { fontSize: 11, color: Colors.muted, fontVariant: ['tabular-nums'] },
  playerControls: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: Spacing.xl, marginTop: Spacing.sm },
  skipBtn: { width: 44, height: 44, alignItems: 'center', justifyContent: 'center' },
  skipText: { fontSize: 10, color: Colors.muted, fontWeight: '700', marginTop: -2 },
  playBtn: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.navy,
    alignItems: 'center',
    justifyContent: 'center',
  },
  playerHint: { fontSize: 12, color: Colors.muted, textAlign: 'center' },
  browserBtn: { marginTop: Spacing.xs },
});
