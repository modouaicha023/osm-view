import React, { useState, useEffect } from "react";
import {
  StyleSheet,
  View,
  Text,
  TouchableOpacity,
  ScrollView,
  ActivityIndicator,
  Alert,
  Dimensions,
} from "react-native";
import Mapbox from "@rnmapbox/maps";
import { Picker } from "@react-native-picker/picker";
import axios, { AxiosError } from "axios";
import { Button, Card, Icon, Overlay } from '@rneui/themed';
import Toast from 'react-native-toast-message';
import { Stack } from 'expo-router';
import * as Location from 'expo-location';

// Debug configuration
const DEBUG = __DEV__;
const log = {
  info: (...args: any[]) => DEBUG && console.log('[INFO]', ...args),
  error: (...args: any[]) => DEBUG && console.error('[ERROR]', ...args),
  warn: (...args: any[]) => DEBUG && console.warn('[WARN]', ...args),
  debug: (...args: any[]) => DEBUG && console.debug('[DEBUG]', ...args),
};

// Mapbox configuration
const MAPBOX_ACCESS_TOKEN = process.env.EXPO_PUBLIC_MAPBOX_ACCESS_TOKEN;
if (!MAPBOX_ACCESS_TOKEN) {
  throw new Error('MAPBOX_ACCESS_TOKEN is not set in environment variables');
}

Mapbox.setAccessToken(MAPBOX_ACCESS_TOKEN);
if (DEBUG) {
  Mapbox.setTelemetryEnabled(false);
  log.info('Mapbox initialized in debug mode');
}

// Replace this URL with your local server IP or production server address
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

// Types
interface MapPoint {
  id: number;
  lat: number;
  lon: number;
  passengers: number;
  distance_to_chateau: number;
  poi_type: string;
  arrival_time: string;
  name: string;
  type?: 'pickup' | 'dropoff';
}

interface Stop {
  coords: [number, number];
  name: string;
  stop_num: number;
  passengers?: number;
}

interface RouteData {
  driver_id: number;
  points: [number, number][];
  stops: Stop[];
  distance: number;
  load: number;
}

interface Stats {
  total_points: number;
  max_distance_km: number;
  num_drivers: number;
  capacity_per_driver: number;
}

interface StatsCardProps {
  title: string;
  value: string | number;
}

interface DriverInfoProps {
  driver: RouteData;
  isSelected: boolean;
  onSelect: () => void;
}

interface Region {
  latitude: number;
  longitude: number;
  latitudeDelta: number;
  longitudeDelta: number;
}

const TimeWindow = ({ label, start, end }: { label: string; start: string; end: string }) => (
  <Card containerStyle={styles.timeCard}>
    <Text style={styles.timeLabel}>{label}</Text>
    <Text style={styles.timeValue}>{start} - {end}</Text>
  </Card>
);
const ErrorMessage = ({ message }: { message: string }) => (
  <View style={{ padding: 10, backgroundColor: '#ffebee', borderRadius: 5, margin: 10 }}>
    <Text style={{ color: '#d32f2f' }}>{message}</Text>
  </View>
);

const StatsCard: React.FC<StatsCardProps> = ({ title, value }) => (
  <Card containerStyle={styles.statsCard}>
    <Text style={styles.statsTitle}>{title}</Text>
    <Text style={styles.statsValue}>{value}</Text>
  </Card>
);

const DriverInfo: React.FC<DriverInfoProps> = ({ driver, isSelected, onSelect }) => (
  <Card containerStyle={[styles.driverCard, isSelected && styles.selectedDriver]}>
    <Text style={styles.driverTitle}>Driver {driver.driver_id}</Text>
    <Text style={styles.driverStats}>Stops: {driver.stops.length - 2}</Text>
    <Button
      title={isSelected ? 'Selected' : 'Select'}
      onPress={onSelect}
      buttonStyle={isSelected ? styles.selectedButton : styles.selectButton}
    />
  </Card>
);

export default function TabsIndex() {
  const [location, setLocation] = useState<Location.LocationObject | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const { status } = await Location.requestForegroundPermissionsAsync();
        if (status !== 'granted') {
          setErrorMsg('Permission to access location was denied');
          return;
        }

        const location = await Location.getCurrentPositionAsync({});
        setLocation(location);
        log.info('Location obtained:', location);
      } catch (error) {
        log.error('Error getting location:', error);
        setErrorMsg('Error getting location');
      }
    })();
  }, []);

  return (
    <View style={styles.container}>
      <Stack.Screen options={{ title: 'OSM View' }} />
      {errorMsg ? (
        <View style={styles.center}>
          <Text style={styles.errorText}>{errorMsg}</Text>
        </View>
      ) : !location ? (
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#4285F4" />
          <Text>Loading map...</Text>
        </View>
      ) : (
        <Mapbox.MapView style={styles.map}>
          <Mapbox.Camera
            zoomLevel={14}
            centerCoordinate={[location.coords.longitude, location.coords.latitude]}
          />
          <Mapbox.UserLocation />
        </Mapbox.MapView>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  center: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
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
  driverCard: {
    width: '30%',
    padding: 8,
  },
  selectedDriver: {
    borderColor: '#4285F4',
    borderWidth: 2,
  },
  driverTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  driverStats: {
    fontSize: 14,
    color: '#666',
  },
  selectButton: {
    backgroundColor: '#4285F4',
  },
  selectedButton: {
    backgroundColor: '#4CAF50',
  },
  markerContainer: {
    width: 30,
    height: 30,
    borderRadius: 15,
    alignItems: 'center',
    justifyContent: 'center',
  },
  markerText: {
    color: 'white',
    fontWeight: 'bold',
  },
  timeWindows: {
    position: 'absolute',
    top: 10,
    left: 0,
    right: 0,
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 10,
  },
  timeCard: {
    width: '45%',
  },
  timeLabel: {
    fontSize: 14,
    color: '#666',
  },
  timeValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  stats: {
    position: 'absolute',
    top: 120,
    right: 10,
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    padding: 10,
    borderRadius: 5,
    maxWidth: 200,
  },
  statsTitle: {
    fontWeight: 'bold',
    marginBottom: 5,
  },
  errorContainer: {
    padding: 20,
    width: 300,
  },
  errorText: {
    color: 'red',
    textAlign: 'center',
    margin: 20,
  },
  statsCard: {
    width: '45%',
  },
  statsValue: {
    fontSize: 16,
    fontWeight: 'bold',
  },
});
