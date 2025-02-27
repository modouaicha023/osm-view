import { Redirect } from 'expo-router';

export default function Index() {
  // Redirect to the main tab
  return <Redirect href="/(tabs)" />;
}
