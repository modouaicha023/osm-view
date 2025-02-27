import { Stack } from "expo-router";
import { useEffect } from "react";
import { Platform, LogBox } from "react-native";

// Ignorer les avertissements liés au Picker sur Android
// (à supprimer une fois que le problème sera résolu dans le package)
useEffect(() => {
  if (Platform.OS === "android") {
    LogBox.ignoreLogs(["Picker has been extracted"]);
  }
}, []);

export default function RootLayout() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
    </Stack>
  );
}
