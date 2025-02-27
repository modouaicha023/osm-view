import { Stack } from "expo-router";
import { useEffect } from "react";
import { Platform, LogBox } from "react-native";
import Toast from 'react-native-toast-message';
import { ThemeProvider } from '@rneui/themed';
import { theme } from "@/theme";

export default function RootLayout() {
  // Ignorer les avertissements liés au Picker sur Android
  useEffect(() => {
    if (Platform.OS === "android") {
      LogBox.ignoreLogs(["Picker has been extracted"]);
    }
  }, []);

  return (
    <ThemeProvider theme={theme}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
      </Stack>
      <Toast />
    </ThemeProvider>
  );
}
