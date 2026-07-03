import React, { useState, useEffect } from "react";
import { 
  View, Text, TextInput, TouchableOpacity, FlatList, Alert, StyleSheet 
} from "react-native";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { MaterialIcons } from "@expo/vector-icons";
import { AI_URL , AUTH_URL } from '../constants/api';

async function fetchWithTokenRefresh(url, options, navigation) {
  let token = await AsyncStorage.getItem("accessToken");
  if (!token) {
    Alert.alert("Auth Error", "User not authenticated. Please login again.");
    navigation.replace("Login");
    return null;
  }

  // Set Authorization header
  options.headers = options.headers || {};
  options.headers["Authorization"] = `Bearer ${token}`;

  let response = await fetch(url, options);

  if (response.status === 401 || response.status === 403) {
    // Try to refresh token
    const refreshToken = await AsyncStorage.getItem("refreshToken");
    if (!refreshToken) {
      Alert.alert("Auth Error", "Session expired. Please login again.");
      navigation.replace("Login");
      return null;
    }

    // Call refresh token endpoint
    const refreshResponse = await fetch(`${AUTH_URL}/refreshToken`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Authorization": `Bearer ${refreshToken}`
      }
    });

    if (refreshResponse.ok) {
      const refreshData = await refreshResponse.json();
      if (refreshData.accessToken) {
        await AsyncStorage.setItem("accessToken", refreshData.accessToken);
        // Retry original request with new token
        options.headers["Authorization"] = `Bearer ${refreshData.accessToken}`;
        response = await fetch(url, options);
        return response;
      } else {
        Alert.alert("Auth Error", "Failed to refresh token. Please login again.");
        navigation.replace("Login");
        return null;
      }
    } else {
      Alert.alert("Auth Error", "Session expired. Please login again.");
      navigation.replace("Login");
      return null;
    }
  }

  return response;
}

export default function EmergencyContacts({ navigation }) {
  const [contacts, setContacts] = useState([]);
  const [name, setName] = useState("");
  const [relation, setRelation] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");

  useEffect(() => {
    loadContacts();
  }, []);

  const loadContacts = async () => {
    try {
      const storedContacts = await AsyncStorage.getItem("emergencyContacts");
      if (storedContacts) {
        try {
          const parsedContacts = JSON.parse(storedContacts);
          setContacts(Array.isArray(parsedContacts) ? parsedContacts : []);
        } catch (parseError) {
          console.error("JSON Parse Error:", parseError);
          setContacts([]);
          await AsyncStorage.removeItem("emergencyContacts");
        }
      }
    } catch (error) {
      console.error("Error loading contacts:", error);
      Alert.alert("Error", "Failed to load contacts from storage.");
    }
  };

  const saveContacts = async (newContacts) => {
    try {
      if (Array.isArray(newContacts)) {
        await AsyncStorage.setItem("emergencyContacts", JSON.stringify(newContacts));
      } else {
        throw new Error("Data format is not an array");
      }
    } catch (error) {
      console.error("Error saving contacts:", error);
      Alert.alert("Error", "Failed to save contacts.");
    }
  };

  const addContact = async () => {
    if (!name.trim() || !relation.trim() || !phone.trim()) {
      Alert.alert("Error", "Name, relation, and phone are required.");
      return;
    }

    const newContact = { name, relation, phone, email, priority: 1 };

    try {
      const response = await fetchWithTokenRefresh(`${AUTH_URL}/emergency/contact`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(newContact),
      }, navigation);

      if (!response) return;

      const data = await response.json();

      if (response.ok && data?.contact) {
        const updatedContacts = [...contacts, data.contact];
        setContacts(updatedContacts);
        await saveContacts(updatedContacts); // saves full contact info

        // 🔥 NEW: Save just the phone number to a separate list
        await updateEmergencyPhoneList(data.contact.phone);

        Alert.alert("Success", "Contact added successfully!");
        [setName, setRelation, setPhone, setEmail].forEach(fn => fn(""));
      } else {
        Alert.alert("Error", data?.error || "Failed to add contact.");
      }
    } catch (error) {
      console.error("Network Error:", error.message);
      Alert.alert("Error", `Could not connect to server: ${error.message}`);
    }
  };

  const deleteContact = async (id) => {
    try {
      const token = await AsyncStorage.getItem("accessToken");
      if (!token) {
        Alert.alert("Auth Error", "User not authenticated. Please login again.");
        navigation.replace("Login");
        return;
      }

      await fetch(`${API_URL}/${id}`, {
        method: "DELETE",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
      });

      const filteredContacts = contacts.filter((contact) => contact._id !== id);
      setContacts(filteredContacts);
      await saveContacts(filteredContacts);
      Alert.alert("Success", "Contact deleted successfully.");
    } catch (error) {
      console.error("Delete Error:", error.message);
      Alert.alert("Error", "Could not delete contact.");
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Emergency Contacts</Text>
      <View style={styles.inputContainer}>
        <TextInput style={styles.input} placeholder="Name" value={name} onChangeText={setName} />
        <TextInput style={styles.input} placeholder="Relation" value={relation} onChangeText={setRelation} />
        <TextInput style={styles.input} placeholder="Phone" value={phone} onChangeText={setPhone} keyboardType="phone-pad" />
        <TextInput style={styles.input} placeholder="Email (optional)" value={email} onChangeText={setEmail} keyboardType="email-address" />
        <TouchableOpacity style={styles.addButton} onPress={addContact}>
          <Text style={styles.addButtonText}>Add Contact</Text>
        </TouchableOpacity>
      </View>
      <FlatList
        data={contacts}
        keyExtractor={(item) => item._id || item.phone || item.name}
        renderItem={({ item }) => (
          <View style={styles.contactItem}>
            <View style={{ flex: 1 }}>
              <Text style={styles.contactName}>{item.name} ({item.relation})</Text>
              <Text style={styles.contactDetails}>📞 {item.phone}</Text>
              {item.email && <Text style={styles.contactDetails}>📧 {item.email}</Text>}
            </View>
            <TouchableOpacity onPress={() => deleteContact(item._id)}>
              <MaterialIcons name="delete" size={24} color="#DC2626" />
            </TouchableOpacity>
          </View>
        )}
      />
      <TouchableOpacity style={styles.homeButton} onPress={() => navigation.navigate("EmergencyAddress")}>
        <Text style={styles.homeButtonText}>Next</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#F0F8FF",
    padding: 20,
  },
  title: {
    fontSize: 26,
    fontWeight: "bold",
    textAlign: "center",
    marginTop:20,
    marginBottom: 25,
    color: "#1E90FF",
  },
  inputContainer: {
    marginBottom: 20,
    backgroundColor: "#ffffff",
    padding: 20,
    borderRadius: 12,
    shadowColor: "#000",
    shadowOpacity: 0.1,
    shadowOffset: { width: 0, height: 2 },
    shadowRadius: 6,
    elevation: 10,
  },
  input: {
    borderWidth: 1,
    borderColor: "#d1d5db",
    paddingHorizontal: 15,
    paddingVertical: 12,
    height: 50,
    borderRadius: 10,
    backgroundColor: "#F9FAFB",
    marginBottom: 15,
    fontSize: 16,
  },
  addButton: {
    backgroundColor: "#1E90FF",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
    marginTop: 10,
  },
  addButtonText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "bold",
  },
  contactItem: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    backgroundColor: "#ffffff",
    padding: 15,
    marginBottom: 12,
    borderRadius: 10,
    shadowColor: "#000",
    shadowOpacity: 0.05,
    shadowOffset: { width: 0, height: 1 },
    shadowRadius: 3,
    elevation: 1,
  },
  contactName: {
    fontSize: 17,
    fontWeight: "bold",
    color: "#111827",
  },
  contactDetails: {
    fontSize: 14,
    color: "#4B5563",
    marginTop: 2,
  },
  homeButton: {
    marginTop: 20,
    backgroundColor: "#1E90FF",
    paddingVertical: 14,
    borderRadius: 10,
    alignItems: "center",
  },
  homeButtonText: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "bold",
  },
});
