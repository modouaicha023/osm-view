import React, { useEffect, useState } from "react";
import { View, StyleSheet } from "react-native";
import MapView, { Marker, Polyline } from "react-native-maps";
import { fetchRoutes } from "../../services/api";
import { RouteData } from "../../types";

const INITIAL_REGION = {
  latitude: 48.450387,
  longitude: -2.044774,
  latitudeDelta: 0.1,
  longitudeDelta: 0.1,
};

export default function ExploreScreen() {
  const [routes, setRoutes] = useState<RouteData[]>([]);

  useEffect(() => {
    const loadRoutes = async () => {
      const data = await fetchRoutes();
      setRoutes(data);
    };
    loadRoutes();
  }, []);

  return (
    <View style={styles.container}>
      <MapView style={styles.map} initialRegion={INITIAL_REGION}>
        {routes.map((route, index) => (
          <Polyline
            key={index}
            coordinates={[
              { latitude: route.lat, longitude: route.lon },
              { latitude: 48.450387, longitude: -2.044774 },
            ]}
            strokeWidth={3}
            strokeColor="blue"
          />
        ))}
        <Marker coordinate={INITIAL_REGION} title="Château de Dinan" />
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
});
