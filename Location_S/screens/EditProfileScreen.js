import React, { useState } from "react";
import {
  View, Text, TextInput, StyleSheet, Image,
  TouchableOpacity, Alert, ScrollView, ActivityIndicator
} from "react-native";
import { Ionicons } from "@expo/vector-icons";
import * as ImagePicker from "expo-image-picker";
import AsyncStorage from "@react-native-async-storage/async-storage";
import { AUTH_URL } from "../constants/api";

const CLOUDINARY_URL = "https://api.cloudinary.com/v1_1/da64byaep/image/upload";
const UPLOAD_PRESET = "ShieldX";

const EditProfileScreen = ({ route, navigation }) => {
  const { user } = route.params;

  const [form, setForm] = useState({
    name: user.name || "",
    email: user.email || "",
    contact1: user.contact1 || "",
    contact2: user.contact2 || "",
  });

  const [profilePicDisplayUrl, setProfilePicDisplayUrl] = useState(user.profilePicUrl || "");
  const [localImageUriToUpload, setLocalImageUriToUpload] = useState(null);
  const [uploadingImage, setUploadingImage] = useState(false);
  const [imageUploadProgress, setImageUploadProgress] = useState(0);

  const handleChange = (key, value) => {
    setForm(prev => ({ ...prev, [key]: value }));
  };

  const pickImage = async () => {
    const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (!permissionResult.granted) {
      Alert.alert("Permission Required", "Please allow access to your photo library.");
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
      allowsEditing: true,
      aspect: [1, 1],
    });

    if (!result.canceled && result.assets.length > 0) {
      const uri = result.assets[0].uri;
      setLocalImageUriToUpload(uri);
      setProfilePicDisplayUrl(uri);
    }
  };

  const handleSave = async () => {
    let finalProfilePicUrl = profilePicDisplayUrl;

    if (localImageUriToUpload) {
      try {
        setUploadingImage(true);
        setImageUploadProgress(0);

        const data = new FormData();
        data.append("file", {
          uri: localImageUriToUpload,
          type: "image/jpeg",
          name: "profile-pic.jpg",
        });
        data.append("upload_preset", UPLOAD_PRESET);

        const res = await fetch(CLOUDINARY_URL, {
          method: "POST",
          body: data,
        });

        const result = await res.json();
        if (!res.ok) {
          throw new Error(result.error?.message || "Cloudinary upload failed");
        }

        finalProfilePicUrl = result.secure_url;
        setUploadingImage(false);
        setLocalImageUriToUpload(null);
        continueWithSave(finalProfilePicUrl);
      } catch (err) {
        console.error("🔥 Cloudinary Upload Error:", err);
        Alert.alert("Upload Failed", err.message || "Image upload failed.");
        setUploadingImage(false);
      }
    } else {
      continueWithSave(finalProfilePicUrl);
    }
  };

const continueWithSave = async (finalProfilePicUrl) => {
    try {
      const token = await AsyncStorage.getItem("accessToken");
      const refreshToken = await AsyncStorage.getItem("refreshToken");
      if (!token) {
        Alert.alert("Error", "Authentication token missing.");
        return;
      }

      const updatedProfileData = { ...form, profilePicUrl: finalProfilePicUrl };
      const backendUrl = `${AUTH_URL}/auth/user-update`;

      const res = await fetch(backendUrl, {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
          "x-refresh-token": refreshToken || "",
        },
        body: JSON.stringify(updatedProfileData),
      });

      if (!res.ok) {
        const errorData = await res.json();
        throw new Error(errorData.message || "Failed to update profile.");
      }

      Alert.alert("Success", "Profile updated successfully.");
      navigation.goBack();
    } catch (backendError) {
      Alert.alert("Error", backendError.message || "Unexpected error occurred.");
    }
  };

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.title}>Edit Your Profile</Text>

      <View style={styles.imageContainer}>
        <TouchableOpacity onPress={pickImage} disabled={uploadingImage}>
          {profilePicDisplayUrl ? (
            <Image source={{ uri: profilePicDisplayUrl }} style={styles.avatar} />
          ) : (
            <View style={styles.imagePlaceholder}>
              <Ionicons name="camera" size={28} color="#999" />
              <Text style={styles.imageText}>Choose Image</Text>
            </View>
          )}
        </TouchableOpacity>
        {uploadingImage && (
          <View style={styles.uploadingOverlay}>
            <ActivityIndicator size="small" color="#1E90FF" />
            <Text style={styles.uploadingText}>{imageUploadProgress}%</Text>
          </View>
        )}
      </View>

      <Text style={styles.label}>Name</Text>
      <TextInput
        style={styles.input}
        value={form.name}
        onChangeText={(text) => handleChange("name", text)}
        placeholder="Enter your name"
      />

      <Text style={styles.label}>Email</Text>
      <TextInput
        style={styles.input}
        value={form.email}
        onChangeText={(text) => handleChange("email", text)}
        placeholder="Enter your email"
        keyboardType="email-address"
        autoCapitalize="none"
      />

      <Text style={styles.subTitle}>Emergency Contacts</Text>

      <Text style={styles.label}>Contact 1</Text>
      <TextInput
        style={styles.input}
        value={form.contact1}
        onChangeText={(text) => handleChange("contact1", text)}
        placeholder="Enter first emergency contact"
        keyboardType="phone-pad"
      />

      <Text style={styles.label}>Contact 2</Text>
      <TextInput
        style={styles.input}
        value={form.contact2}
        onChangeText={(text) => handleChange("contact2", text)}
        placeholder="Enter second emergency contact"
        keyboardType="phone-pad"
      />

      <TouchableOpacity
        style={styles.saveButton}
        onPress={handleSave}
        disabled={uploadingImage}
      >
        <Text style={styles.saveButtonText}>
          {uploadingImage ? `Uploading Image... ${imageUploadProgress}%` : "Save Changes"}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

export default EditProfileScreen;

const styles = StyleSheet.create({
  container: {
    backgroundColor: "#fff",
    padding: 20,
    paddingBottom: 40
  },
  title: {
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 20,
    textAlign: "center",
    color: "#1E90FF"
  },
  subTitle: {
    fontSize: 18,
    fontWeight: "bold",
    marginTop: 30,
    marginBottom: 10,
    color: "#333"
  },
  imageContainer: {
    alignItems: "center",
    marginBottom: 20,
    position: 'relative',
  },
  avatar: {
    width: 100,
    height: 100,
    borderRadius: 50,
    borderWidth: 2,
    borderColor: "#ccc"
  },
  imagePlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: "#f0f0f0",
    justifyContent: "center",
    alignItems: "center",
    borderWidth: 1,
    borderColor: "#ccc"
  },
  imageText: {
    fontSize: 12,
    color: "#777",
    marginTop: 4
  },
  uploadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(255,255,255,0.7)',
    borderRadius: 50,
    justifyContent: 'center',
    alignItems: 'center',
  },
  uploadingText: {
    marginTop: 5,
    fontSize: 12,
    color: '#333',
  },
  label: {
    fontSize: 14,
    color: "#333",
    marginBottom: 5,
    marginTop: 10
  },
  input: {
    borderWidth: 1,
    borderColor: "#ccc",
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    marginBottom: 10,
    backgroundColor: "#f9f9f9"
  },
  saveButton: {
    backgroundColor: "#1E90FF",
    paddingVertical: 14,
    borderRadius: 8,
    marginTop: 20
  },
  saveButtonText: {
    color: "#fff",
    fontWeight: "bold",
    textAlign: "center",
    fontSize: 16
  }
});
