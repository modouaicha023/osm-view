import React from "react";
import { View, Text, StyleSheet, FlatList } from "react-native";
import { RouteProp } from "@react-navigation/native";
import { RootStackParamList } from "../types";

type RouteResultScreenRouteProp = RouteProp<RootStackParamList, "RouteResult">;

interface RouteResultScreenProps {
  route: RouteResultScreenRouteProp;
}

const RouteResultScreen: React.FC<RouteResultScreenProps> = ({ route }) => {
  const { routes } = route.params;

  const renderRoute = ({ item, index }: { item: any; index: number }) => (
    <View style={styles.routeContainer}>
      <Text style={styles.routeTitle}>Vehicle {index + 1}</Text>
      <FlatList
        data={item}
        keyExtractor={(point, idx) => idx.toString()}
        renderItem={({ item: point }) => (
          <View style={styles.pointItem}>
            <Text>
              Point: {point.name}
              {"\n"}Lat: {point.lat}, Lon: {point.lon}
              {"\n"}Arrival: {point.arrival_time}
            </Text>
          </View>
        )}
      />
    </View>
  );

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Optimized Routes</Text>
      <FlatList
        data={routes}
        keyExtractor={(_, index) => index.toString()}
        renderItem={renderRoute}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 10,
    backgroundColor: "#f0f0f0",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
    marginVertical: 20,
  },
  routeContainer: {
    backgroundColor: "white",
    borderRadius: 10,
    padding: 15,
    marginBottom: 15,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  routeTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 10,
  },
  pointItem: {
    borderBottomWidth: 1,
    borderBottomColor: "#eee",
    paddingVertical: 10,
  },
});

export default RouteResultScreen;
