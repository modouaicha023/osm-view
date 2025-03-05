import React from "react";
import { NavigationContainer } from "@react-navigation/native";
import { createStackNavigator } from "@react-navigation/stack";
import { RootStackParamList } from "@/types";
import HomeScreen from "@/screens/HomeScreen";
import MapScreen from "@/screens/MapScreen";
import RouteResultScreen from "@/screens/RouteResultScreen";

const Stack = createStackNavigator<RootStackParamList>();

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator initialRouteName="Home">
        <Stack.Screen
          name="Home"
          component={HomeScreen}
          options={{ title: "Route Optimization" }}
        />
        <Stack.Screen
          name="Map"
          component={MapScreen}
          options={{ title: "Select Delivery Points" }}
        />
        <Stack.Screen
          name="RouteResult"
          component={RouteResultScreen}
          options={{ title: "Optimized Routes" }}
        />
      </Stack.Navigator>
    </NavigationContainer>
  );
}
