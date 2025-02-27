import React, { useState, useEffect } from "react";
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
} from "react-native";
import MapView, { Marker, Polyline } from "react-native-maps";
import { Picker } from "@react-native-picker/picker";
import axios from "axios";
import { Point, Route, Region } from "@/types";

// Remplacez cette URL par l'adresse IP de votre serveur local ou votre serveur de production
const API_URL = "http://192.168.1.13:5000/api";

const colors = [
  "#4CAF50",
  "#9C27B0",
  "#FF9800",
  "#5D9CEC",
  "#8B0000",
  "#000000",
  "#FFC0CB",
];

export default function TabOneScreen() {
  const [loading, setLoading] = useState<boolean>(false);
  const [points, setPoints] = useState<Point[]>([]);
  const [routes, setRoutes] = useState<Route[]>([]);
  const [selectedDriver, setSelectedDriver] = useState<number>(0);
  const [numDrivers, setNumDrivers] = useState<number>(3);
  const [capacity, setCapacity] = useState<number>(8);
  const [region, setRegion] = useState<Region>({
    latitude: 48.45038746219548,
    longitude: -2.0447748346342434,
    latitudeDelta: 0.1,
    longitudeDelta: 0.1,
  });

  // Charger les points au démarrage
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

  const optimizeRoutes = async () => {
    try {
      setLoading(true);
      const response = await axios.post(`${API_URL}/optimize`, {
        num_drivers: numDrivers,
        capacity_per_driver: capacity,
        max_distance_km: 15,
      });

      setRoutes(response.data.routes);
      setLoading(false);

      Alert.alert(
        "Optimisation réussie",
        `Distance totale: ${response.data.total_distance.toFixed(2)} km\n` +
          `Passagers: ${response.data.total_passengers}`
      );
    } catch (error) {
      console.error("Error optimizing routes:", error);
      setLoading(false);
      Alert.alert("Erreur", "Échec de l'optimisation des itinéraires");
    }
  };

  const getDriverRoute = (): Route | null => {
    if (!routes || routes.length === 0) return null;
    return routes.find((r) => r.driver_id === selectedDriver) || routes[0];
  };

  const renderDriverRoute = () => {
    const route = getDriverRoute();
    if (!route) return null;

    const routePoints = route.points.map((point) => ({
      latitude: point[0],
      longitude: point[1],
    }));

    const color = colors[selectedDriver % colors.length];

    return (
      <>
        <Polyline
          coordinates={routePoints}
          strokeColor={color}
          strokeWidth={4}
        />
        {route.stops.map((stop, index) => (
          <Marker
            key={`stop-${index}`}
            coordinate={{
              latitude: stop.coords[0],
              longitude: stop.coords[1],
            }}
            title={stop.name}
            description={`Arrêt ${index}`}
            pinColor={
              index === 0 || index === route.stops.length - 1 ? "red" : color
            }
          />
        ))}
      </>
    );
  };

  const renderDriverInfo = () => {
    const route = getDriverRoute();
    if (!route) return null;

    return (
      <View style={styles.driverInfo}>
        <Text style={styles.driverTitle}>Chauffeur {selectedDriver}</Text>
        <Text>Distance: {route.distance.toFixed(2)} km</Text>
        <Text>Passagers: {route.load}</Text>
        <Text>Arrêts: {route.stops.length - 2}</Text>{" "}
        {/* -2 pour exclure départ/retour au château */}
      </View>
    );
  };

  return (
    <View style={styles.container}>
      <MapView
        style={styles.map}
        region={region}
        onRegionChangeComplete={setRegion}
      >
        {/* Château (dépôt) */}
        <Marker
          coordinate={{
            latitude: 48.45038746219548,
            longitude: -2.0447748346342434,
          }}
          title="Château de Dinan"
          description="Point de départ"
          pinColor="red"
        />

        {/* Points de ramassage */}
        {points.map((point) => (
          <Marker
            key={`point-${point.id}`}
            coordinate={{
              latitude: point.lat,
              longitude: point.lon,
            }}
            title={point.name}
            description={`${point.passengers} passagers`}
            opacity={0.7}
            pinColor="blue"
          />
        ))}

        {/* Itinéraire du chauffeur sélectionné */}
        {renderDriverRoute()}
      </MapView>

      <View style={styles.controls}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          <View style={styles.configSection}>
            <Text style={styles.label}>Nombre de chauffeurs:</Text>
            <Picker
              selectedValue={numDrivers.toString()}
              style={styles.picker}
              onValueChange={(value) => setNumDrivers(Number(value))}
              enabled={!loading}
            >
              {[1, 2, 3, 4, 5].map((num) => (
                <Picker.Item
                  key={`drivers-${num}`}
                  label={`${num}`}
                  value={num.toString()}
                />
              ))}
            </Picker>
          </View>

          <View style={styles.configSection}>
            <Text style={styles.label}>Capacité par chauffeur:</Text>
            <Picker
              selectedValue={capacity.toString()} // Convert to string
              style={styles.picker}
              onValueChange={(value) => setCapacity(Number(value))}
              enabled={!loading}
            >
              {[4, 6, 8, 10, 12].map((num) => (
                <Picker.Item
                  key={`capacity-${num}`}
                  label={`${num}`}
                  value={num.toString()} // Convert to string
                />
              ))}
            </Picker>
          </View>

          <TouchableOpacity
            style={[styles.button, loading && styles.disabledButton]}
            onPress={optimizeRoutes}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.buttonText}>Optimiser</Text>
            )}
          </TouchableOpacity>
        </ScrollView>
      </View>

      {routes.length > 0 && (
        <View style={styles.driverSelector}>
          <Text style={styles.label}>Sélectionner chauffeur:</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false}>
            {routes.map((route) => (
              <TouchableOpacity
                key={`driver-${route.driver_id}`}
                style={[
                  styles.driverButton,
                  { backgroundColor: colors[route.driver_id % colors.length] },
                  selectedDriver === route.driver_id &&
                    styles.selectedDriverButton,
                ]}
                onPress={() => setSelectedDriver(route.driver_id)}
              >
                <Text style={styles.driverButtonText}>{route.driver_id}</Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>
      )}

      {renderDriverInfo()}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  controls: {
    position: "absolute",
    top: 50,
    left: 0,
    right: 0,
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    padding: 10,
    borderRadius: 5,
    margin: 10,
  },
  configSection: {
    marginRight: 15,
  },
  label: {
    fontWeight: "bold",
    marginBottom: 5,
  },
  picker: {
    width: 120,
    height: 40,
  },
  button: {
    backgroundColor: "#4285F4",
    padding: 10,
    borderRadius: 5,
    justifyContent: "center",
    alignItems: "center",
    height: 40,
    minWidth: 100,
  },
  disabledButton: {
    backgroundColor: "#AAAAAA",
  },
  buttonText: {
    color: "#fff",
    fontWeight: "bold",
  },
  driverSelector: {
    position: "absolute",
    bottom: 160,
    left: 0,
    right: 0,
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    padding: 10,
    borderRadius: 5,
    margin: 10,
  },
  driverButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: "center",
    alignItems: "center",
    marginRight: 10,
  },
  selectedDriverButton: {
    borderWidth: 3,
    borderColor: "#fff",
  },
  driverButtonText: {
    color: "#fff",
    fontWeight: "bold",
  },
  driverInfo: {
    position: "absolute",
    bottom: 50,
    left: 0,
    right: 0,
    backgroundColor: "rgba(255, 255, 255, 0.9)",
    padding: 15,
    borderRadius: 5,
    margin: 10,
  },
  driverTitle: {
    fontWeight: "bold",
    fontSize: 16,
    marginBottom: 5,
  },
});
