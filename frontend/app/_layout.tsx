import { Stack } from "expo-router";

export default function Layout() {
  return (
    <Stack>
      <Stack.Screen name="(tabs)/index" options={{ title: "Accueil" }} />
      <Stack.Screen name="(tabs)/explore" options={{ title: "Carte" }} />
    </Stack>
  );
}
