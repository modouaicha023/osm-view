import React, { useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  TextInput,
} from "react-native";
import { StackNavigationProp } from "@react-navigation/stack";
import { RootStackParamList, LatLng } from "../types";

type HomeScreenNavigationProp = StackNavigationProp<RootStackParamList, "Home">;

interface HomeScreenProps {
  navigation: HomeScreenNavigationProp;
}

const HomeScreen: React.FC<HomeScreenProps> = ({ navigation }) => {
  const [startPoint, setStartPoint] = useState<LatLng | undefined>(undefined);
  const [vehicleCount, setVehicleCount] = useState("2");

  const handleSelectStartPoint = () => {
    navigation.navigate("Map", { startPoint });
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Route Optimization</Text>

      <View style={styles.inputContainer}>
        <Text>Start Point Coordinates:</Text>
        <TextInput
          style={styles.input}
          placeholder="Latitude"
          keyboardType="numeric"
          value={startPoint?.latitude.toString()}
          onChangeText={(text) =>
            setStartPoint((prev) => ({
              ...(prev || {}),
              latitude: parseFloat(text),
            }))
          }
        />
        <TextInput
          style={styles.input}
          placeholder="Longitude"
          keyboardType="numeric"
          value={startPoint?.longitude.toString()}
          onChangeText={(text) =>
            setStartPoint((prev) => ({
              ...(prev || {}),
              longitude: parseFloat(text),
            }))
          }
        />

        <Text>Number of Vehicles:</Text>
        <TextInput
          style={styles.input}
          placeholder="Number of Vehicles"
          keyboardType="numeric"
          value={vehicleCount}
          onChangeText={setVehicleCount}
        />
      </View>

      <TouchableOpacity style={styles.button} onPress={handleSelectStartPoint}>
        <Text style={styles.buttonText}>Select Delivery Points</Text>
      </TouchableOpacity>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    padding: 20,
    justifyContent: "center",
    backgroundColor: "#f0f0f0",
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    textAlign: "center",
    marginBottom: 20,
  },
  inputContainer: {
    marginBottom: 20,
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    padding: 10,
    marginVertical: 5,
    borderRadius: 5,
  },
  button: {
    backgroundColor: "#007bff",
    padding: 15,
    borderRadius: 5,
    alignItems: "center",
  },
  buttonText: {
    color: "white",
    fontWeight: "bold",
  },
});

export default HomeScreen;
