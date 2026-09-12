import { DefaultTheme, Stack, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { useEffect } from 'react';

import { AuthProvider, useAuth } from '../lib/auth';
import { Colors } from '../lib/theme';

SplashScreen.preventAutoHideAsync();

function RootNavigator() {
  const { booted } = useAuth();

  useEffect(() => {
    if (booted) {
      SplashScreen.hideAsync();
    }
  }, [booted]);

  if (!booted) {
    return null;
  }

  const navTheme = {
    ...DefaultTheme,
    colors: {
      ...DefaultTheme.colors,
      primary: Colors.navy,
      background: Colors.bg,
      card: Colors.card,
      text: Colors.text,
      border: Colors.border,
    },
  };

  return (
    <ThemeProvider value={navTheme}>
      <Stack
        screenOptions={{
          headerTintColor: Colors.navy,
          headerTitleStyle: { fontWeight: '800' },
          headerStyle: { backgroundColor: Colors.card },
          contentStyle: { backgroundColor: Colors.bg },
        }}>
        <Stack.Screen name="index" options={{ headerShown: false }} />
        <Stack.Screen name="login" options={{ headerShown: false }} />
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="list/[kind]" options={{ title: 'Records' }} />
        <Stack.Screen
          name="prayers/new"
          options={{ title: 'New Prayer Request', presentation: 'modal', headerBackButtonDisplayMode: 'minimal' }}
        />
      </Stack>
    </ThemeProvider>
  );
}

export default function RootLayout() {
  return (
    <AuthProvider>
      <RootNavigator />
    </AuthProvider>
  );
}