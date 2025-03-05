import React, { useState } from "react";
import MapView, { Marker, PROVIDER_GOOGLE } from "react-native-maps";
import {
  View,
  Text,
  StyleSheet,
  Dimensions,
  TouchableOpacity,
} from "react-native";
import { StackNavigationProp } from "@react-navigation/stack";
import { RouteProp } from "@react-navigation/native";
import { RootStackParamList, LatLng } from "../types";
import axios from "axios";

type MapScreenNavigationProp = StackNavigationProp<RootStackParamList, "Map">;
type MapScreenRouteProp = RouteProp<RootStackParamList, "Map">;

interface MapScreenProps {
  navigation: MapScreenNavigationProp;
  route: MapScreenRouteProp;
}

const MapScreen: React.FC<MapScreenProps> = ({ navigation, route }) => {
  const [deliveryPoints, setDeliveryPoints] = useState<LatLng[]>([]);
  const startPoint = route.params?.startPoint;

  const handleMapPress = (event: any) => {
    const { coordinate } = event.nativeEvent;
    setDeliveryPoints((prev) => [...prev, coordinate]);
  };

  const optimizeRoute = async () => {
    try {
      const response = await axios.post(
        "http://192.168.253.184:8000/optimize_route",
        {
          start_point: startPoint,
          delivery_points: deliveryPoints,
          vehicle_count: 2,
        }
      );

      navigation.navigate("RouteResult", { routes: response.data.routes });
    } catch (error) {
      console.error("Route optimization error:", error);
      // Handle error (show alert, etc.)
    }
  };

  return (
    <View style={styles.container}>
      <MapView
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        initialRegion={{
          latitude: startPoint?.latitude || 48.450387,
          longitude: startPoint?.longitude || -2.044774,
          latitudeDelta: 0.1,
          longitudeDelta: 0.1,
        }}
        onPress={handleMapPress}
      >
        {startPoint && (
          <Marker
            coordinate={startPoint}
            pinColor="green"
            title="Start Point"
          />
        )}
        {deliveryPoints.map((point, index) => (
          <Marker
            key={index}
            coordinate={point}
            title={`Delivery Point ${index + 1}`}
          />
        ))}
      </MapView>

      <View style={styles.buttonContainer}>
        <Text style={styles.pointsText}>
          Delivery Points: {deliveryPoints.length}
        </Text>
        <TouchableOpacity
          style={styles.optimizeButton}
          onPress={optimizeRoute}
          disabled={deliveryPoints.length < 2}
        >
          <Text style={styles.buttonText}>Optimize Route</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    width: Dimensions.get("window").width,
    height: Dimensions.get("window").height - 100,
  },
  buttonContainer: {
    position: "absolute",
    bottom: 0,
    width: "100%",
    padding: 10,
    backgroundColor: "white",
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
  },
  pointsText: {
    fontSize: 16,
  },
  optimizeButton: {
    backgroundColor: "#007bff",
    padding: 10,
    borderRadius: 5,
  },
  buttonText: {
    color: "white",
  },
});

export default MapScreen;
