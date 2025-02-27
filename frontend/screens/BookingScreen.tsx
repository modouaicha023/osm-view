import React, { useState } from "react";
import { View, Text, TextInput, Button, StyleSheet } from "react-native";

export default function BookingScreen() {
  const [name, setName] = useState<string>("");
  const [passengers, setPassengers] = useState<string>("");

  const handleBooking = () => {
    console.log("Réservation de", name, "avec", passengers, "passagers.");
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Réserver une place</Text>
      <TextInput
        style={styles.input}
        placeholder="Nom"
        value={name}
        onChangeText={setName}
      />
      <TextInput
        style={styles.input}
        placeholder="Nombre de passagers"
        value={passengers}
        onChangeText={setPassengers}
        keyboardType="numeric"
      />
      <Button title="Valider" onPress={handleBooking} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: "center", padding: 20 },
  title: { fontSize: 20, marginBottom: 10 },
  input: { borderWidth: 1, padding: 10, marginBottom: 10, borderRadius: 5 },
});
