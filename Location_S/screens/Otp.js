import React, { useRef, useState } from "react";
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Image, ToastAndroid, Alert } from "react-native";
import { AUTH_URL } from '../constants/api';

const Otp = ({ navigation, route }) => {
  const { phoneNo } = route.params;
  const [otp, setOtp] = useState(["", "", "", "", ""]);
  const [verified, setVerified] = useState(false);
  const [loading, setLoading] = useState(false);
  const [resending, setResending] = useState(false);

  const inputs = [useRef(), useRef(), useRef(), useRef(), useRef()];

  const handleChange = (text, idx) => {
    if (/^\d?$/.test(text)) {
      const newOtp = [...otp];
      newOtp[idx] = text;
      setOtp(newOtp);

      if (text && idx < 4) {
        inputs[idx + 1].current.focus();
      } else if (!text && idx > 0) {
        inputs[idx - 1].current.focus();
      }
    }
  };

  const handleVerify = async () => {
    const otpCode = otp.join("");

    if (otpCode.length < 5) {
      Alert.alert("Error", "Please enter the full OTP.");
      return;
    }

    setLoading(true);
    try {
      const verifyResponse = await fetch(`${AUTH_URL}/verify-phone-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phoneNo, otp: otpCode }),
      });

      const data = await verifyResponse.json();

      if (verifyResponse.ok && data.success) {
        ToastAndroid.show("Phone number verified!", ToastAndroid.LONG);
        setVerified(true);
        navigation.navigate("Login");
      } else {
        Alert.alert("Invalid OTP", data.message || "Verification failed.");
      }
    } catch (err) {
      Alert.alert("Error", "Server error. Please try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setResending(true);
    try {
      const response = await fetch(`${AUTH_URL}/send-phone-otp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phoneNo }),
      });

      const data = await response.json();
      if (response.ok && data.success) {
        ToastAndroid.show("OTP resent to your phone", ToastAndroid.LONG);
      } else {
        Alert.alert("Error", data.message || "Failed to resend OTP.");
      }
    } catch (err) {
      Alert.alert("Error", "Could not resend OTP. Try again.");
    } finally {
      setResending(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={{ flexDirection: "column", marginBottom: 20 }}>
        <Image source={require("../assets/verify.png")} style={{ width: 380, height: 380, resizeMode: "contain" }} />
      </View>

      <Text style={styles.title}>Phone OTP Verification</Text>
      <Text style={styles.subtitle}>Enter the 5-digit code sent to {phoneNo}</Text>

      <View style={styles.otpContainer}>
        {otp.map((digit, idx) => (
          <TextInput
            key={idx}
            ref={inputs[idx]}
            style={styles.otpInput}
            keyboardType="number-pad"
            maxLength={1}
            value={digit}
            onChangeText={text => handleChange(text, idx)}
            placeholder="-"
            placeholderTextColor="#bbb"
            autoFocus={idx === 0}
          />
        ))}
      </View>

      <TouchableOpacity style={[styles.button, loading && { backgroundColor: "#999" }]} onPress={handleVerify} disabled={loading || verified}>
        <Text style={styles.buttonText}>{loading ? "Verifying..." : verified ? "Verified ✅" : "Verify"}</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={handleResendOtp} disabled={resending} style={{ marginTop: 15 }}>
        <Text style={{ color: "#1E90FF", fontWeight: "bold", fontSize: 16 }}>
          {resending ? "Resending OTP..." : "Resend OTP"}
        </Text>
      </TouchableOpacity>

      {verified && <Text style={styles.successText}>Phone number verified successfully!</Text>}
    </View>
  );
};

export default Otp;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#fff",
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  title: {
    fontSize: 26,
    color: "#1E90FF",
    fontWeight: "bold",
    marginBottom: 10,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 15,
    color: "#8d99ae",
    marginBottom: 30,
    textAlign: "center",
  },
  otpContainer: {
    flexDirection: "row",
    justifyContent: "space-between",
    marginBottom: 25,
    marginHorizontal: 10,
  },
  otpInput: {
    width: 48,
    height: 55,
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 10,
    textAlign: "center",
    fontSize: 22,
    color: "#333",
    backgroundColor: "#f6f7fb",
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 2,
  },
  button: {
    backgroundColor: "#1E90FF",
    paddingVertical: 15,
    borderRadius: 10,
  },
  buttonText: {
    color: "#fff",
    fontSize: 16,
    textAlign: "center",
    fontWeight: "bold",
  },
  successText: {
    marginTop: 20,
    fontSize: 16,
    color: "green",
    textAlign: "center",
  },
});
