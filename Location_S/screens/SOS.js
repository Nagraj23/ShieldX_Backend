import { useEffect, useState, useRef } from "react";
import {
  View, Text, TouchableOpacity, StyleSheet, Animated, StatusBar, SafeAreaView, Platform,
  Alert
} from "react-native";
import { Audio } from "expo-av";
import * as Location from "expo-location";
import AsyncStorage from "@react-native-async-storage/async-storage";

export default function SOS() {
  const [sound, setSound] = useState(null);
  const outerCircle = useRef(new Animated.Value(1)).current;
  const middleCircle = useRef(new Animated.Value(1)).current;
  const innerCircle = useRef(new Animated.Value(1)).current;

  const API_URL = "http://192.168.124.199:8000/api/sos";
  const EMERGENCY_CONTACTS = ["nagrajnandal43@gmail.com", "+7620101655"];

  useEffect(() => {
    setupAudio();
    return () => {
      if (sound) {
        sound.unloadAsync();
      }
    };
  }, []);

  const setupAudio = async () => {
    try {
      const { status } = await Audio.requestPermissionsAsync();
      if (status !== "granted") {
        Alert.alert("Permission Required", "Audio permission is needed for SOS alerts");
        return;
      }
      await Audio.setAudioModeAsync({
        playsInSilentModeIOS: true,
        staysActiveInBackground: true,
      });
    } catch (error) {
      console.error("Error setting up audio:", error);
    }
  };

  const playAlertSound = async () => {
    try {
      if (sound) {
        await sound.unloadAsync();
      }
      const { sound: newSound } = await Audio.Sound.createAsync(
        require("../assets/alert.mp3"),
        { shouldPlay: true, isLooping: true }
      );
      setSound(newSound);
    } catch (error) {
      console.error("Error playing alert sound:", error);
    }
  };

  const fetchSOS = async () => {
    try {
      // लोकेशन परमिशन चेक करें
      let { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== "granted") {
        Alert.alert("Permission Required", "Location permission is needed for SOS alerts");
        return;
      }

      // लोकेशन प्राप्त करें
      let location = await Location.getCurrentPositionAsync({});
      const { latitude, longitude } = location.coords;

      // SOS अलर्ट भेजें
      const response = await fetch(`${API_URL}/sos`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          lat: latitude,
          lon: longitude,
          contacts: EMERGENCY_CONTACTS
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to send SOS");
      }

      // अलर्ट साउंड प्ले करें
      await playAlertSound();

      Alert.alert(
        "SOS Alert Sent",
        "Your emergency contacts have been notified with your location."
      );

    } catch (error) {
      console.error("Error in SOS function:", error);
      Alert.alert("Error", "Failed to send SOS alert. Please try again.");
    }
  };

  // एनिमेशन सेटअप
  useEffect(() => {
    const pulse = Animated.sequence([
      Animated.parallel([
        Animated.timing(outerCircle, { toValue: 1.3, duration: 1000, useNativeDriver: true }),
        Animated.timing(middleCircle, { toValue: 1.2, duration: 1000, useNativeDriver: true }),
        Animated.timing(innerCircle, { toValue: 1.1, duration: 1000, useNativeDriver: true }),
      ]),
      Animated.parallel([
        Animated.timing(outerCircle, { toValue: 1, duration: 1000, useNativeDriver: true }),
        Animated.timing(middleCircle, { toValue: 1, duration: 1000, useNativeDriver: true }),
        Animated.timing(innerCircle, { toValue: 1, duration: 1000, useNativeDriver: true }),
      ]),
    ]);

    Animated.loop(pulse).start();
  }, []);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />
      <Text style={styles.appName}>ShieldX</Text>
      <Text style={styles.message}>
        Press the SOS button in case of emergency
      </Text>
      <View style={styles.buttonContainer}>
        <Animated.View style={[styles.circle, styles.outerCircle, { transform: [{ scale: outerCircle }] }]} />
        <Animated.View style={[styles.circle, styles.middleCircle, { transform: [{ scale: middleCircle }] }]} />
        <Animated.View style={[styles.circle, styles.innerCircle, { transform: [{ scale: innerCircle }] }]} />
        <TouchableOpacity
          activeOpacity={0.8}
          style={styles.sosButton}
          onPress={fetchSOS}
        >
          <Text style={styles.sosText}>SOS</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: "white", paddingHorizontal: 16 },
  appName: { fontSize: 34, fontWeight: "600", color: "#6666ff", textAlign: "center", marginTop: Platform.OS === "android" ? StatusBar.currentHeight : 0, marginBottom: 16 },
  message: { fontSize: 22, color: "#1F2937", textAlign: "center", marginBottom: 32 },
  buttonContainer: { alignItems: "center", justifyContent: "center", height: 400 },
  circle: { position: "absolute", borderRadius: 999 },
  outerCircle: { width: 280, height: 280, backgroundColor: "#ccccff" },
  middleCircle: { width: 220, height: 220, backgroundColor: "#b3b3ff" },
  innerCircle: { width: 160, height: 160, backgroundColor: "#9999ff" },
  sosButton: { width: 112, height: 112, borderRadius: 56, backgroundColor: "#6666ff", alignItems: "center", justifyContent: "center", elevation: 8, shadowColor: "#000", shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 4.65 },
  sosText: { color: "white", fontSize: 24, fontWeight: "bold" },
}); 