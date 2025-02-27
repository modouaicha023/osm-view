import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import MapScreen from "@/screens/MapScreen";
import BookingScreen from "@/screens/BookingScreen";

const Stack = createStackNavigator();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="Carte" component={MapScreen} />
        <Stack.Screen name="Réservation" component={BookingScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
