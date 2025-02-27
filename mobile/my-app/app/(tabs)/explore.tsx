import React, { useState, useEffect } from "react";
import {
  StyleSheet,
  View,
  Text,
  FlatList,
  ActivityIndicator,
  Alert,
} from "react-native";
import axios from "axios";
import { Point } from "../../types";

// Remplacez cette URL par l'adresse IP de votre serveur local ou votre serveur de production
const API_URL = "http://192.168.1.13:5000/api";

export default function ExploreScreen() {
  const [loading, setLoading] = useState<boolean>(false);
  const [points, setPoints] = useState<Point[]>([]);

  useEffect(() => {
    fetchPoints();
  }, []);

  const fetchPoints = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_URL}/points`);
      setPoints(response.data);
      setLoading(false);
    } catch (error) {
      console.error("Error fetching points:", error);
      setLoading(false);
      Alert.alert("Erreur", "Impossible de charger les points");
    }
  };

  const renderPointItem = ({ item }: { item: Point }) => (
    <View style={styles.pointItem}>
      <Text style={styles.pointName}>{item.name}</Text>
      <Text>
        Coordonnées: {item.lat.toFixed(5)}, {item.lon.toFixed(5)}
      </Text>
      <Text>Passagers: {item.passengers}</Text>
    </View>
  );

  if (loading && points.length === 0) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#4285F4" />
        <Text style={styles.loadingText}>Chargement des points...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Points de Ramassage</Text>
      <FlatList
        data={points}
        keyExtractor={(item) => `point-${item.id}`}
        renderItem={renderPointItem}
        contentContainerStyle={styles.listContainer}
        ListEmptyComponent={
          <Text style={styles.emptyText}>Aucun point disponible</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 16,
    backgroundColor: "#f5f5f5",
  },
  centered: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
  },
  title: {
    fontSize: 22,
    fontWeight: "bold",
    marginBottom: 16,
  },
  listContainer: {
    paddingBottom: 20,
  },
  pointItem: {
    backgroundColor: "#fff",
    padding: 16,
    borderRadius: 8,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2,
  },
  pointName: {
    fontSize: 18,
    fontWeight: "bold",
    marginBottom: 8,
  },
  emptyText: {
    textAlign: "center",
    fontSize: 16,
    color: "#888",
    marginTop: 50,
  },
});
