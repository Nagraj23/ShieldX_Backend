import React, { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, Alert } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useNavigation } from '@react-navigation/native';
import { AUTH_URL } from '../constants/api';

export default function SecurityCodeScreen() {
  const [code, setCode] = useState(['', '', '', '', '', '']); // 6 digits
  const navigation = useNavigation();
  const inputRefs = useRef([]);

  const handleChange = (text, index) => {
    const newCode = [...code];
    newCode[index] = text;
    setCode(newCode);

    if (text && index < 5) {
      inputRefs.current[index + 1]?.focus();
    } else if (!text && index > 0) {
      inputRefs.current[index - 1]?.focus();
    }
  };

  const handleVerify = async () => {
    const enteredCode = code.join('');

    if (enteredCode.length !== 6) {
      Alert.alert('Invalid Code', 'Please enter a 6-digit security PIN.');
      return;
    }

    try {
      const accessToken = await AsyncStorage.getItem('accessToken');
      const refreshToken = await AsyncStorage.getItem('refreshToken');

      if (!accessToken) {
        Alert.alert('Authentication Error', 'You are not logged in. Please log in again.');
        navigation.replace('Star');
        return;
      }

      const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`,
      };

      if (refreshToken) {
        headers['x-refresh-token'] = refreshToken;
      }

      const response = await fetch(`${AUTH_URL}/auth/user-update`, {
        method: 'PATCH',
        headers,
        body: JSON.stringify({ securityCode: enteredCode }),
      });

      const newAccessTokenFromHeader = response.headers.get('Authorization');
      if (newAccessTokenFromHeader?.startsWith('Bearer ')) {
        const newTokenValue = newAccessTokenFromHeader.split(' ')[1];
        if (newTokenValue && newTokenValue !== accessToken) {
          await AsyncStorage.setItem('accessToken', newTokenValue);
          console.log('✅ Updated Access Token in AsyncStorage.');
        }
      }

      const responseData = await response.json();

      if (response.ok) {
        Alert.alert('Success', 'Security PIN set successfully!');
        navigation.replace('MainTabs');
      } else {
        Alert.alert('Error', responseData.error || 'Failed to update security code. Please try again.');
      }
    } catch (error) {
      console.error('Unexpected error:', error);
      Alert.alert('Error', 'An unexpected error occurred. Please check your network and try again.');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Set Up Security PIN</Text>

      <View style={styles.iconPlaceholder}>
        <Text style={{ fontSize: 36 }}>🔐</Text>
      </View>

      <Text style={styles.instruction}>Choose a 6-Digit PIN for Your Account</Text>
      <Text style={styles.subText}>
        This PIN will be used periodically to ensure your safety like a SECURITY PIN.
      </Text>

      <View style={styles.codeContainer}>
        {code.map((digit, index) => (
          <TextInput
            key={index}
            ref={el => (inputRefs.current[index] = el)}
            style={styles.input}
            keyboardType="numeric"
            maxLength={1}
            value={digit}
            onChangeText={(text) => handleChange(text, index)}
            onKeyPress={({ nativeEvent }) => {
              if (nativeEvent.key === 'Backspace' && !code[index] && index > 0) {
                inputRefs.current[index - 1]?.focus();
              }
            }}
          />
        ))}
      </View>

      <TouchableOpacity style={styles.button} onPress={handleVerify}>
        <Text style={styles.buttonText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#ffffff',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    marginBottom: 10,
    color: '#1e90ff'
  },
  iconPlaceholder: {
    marginVertical: 20
  },
  instruction: {
    fontSize: 18,
    fontWeight: '600',
    marginBottom: 8,
    color: '#1e90ff',
    textAlign: 'center'
  },
  subText: {
    fontSize: 14,
    color: '#444',
    textAlign: 'center',
    marginBottom: 20,
    paddingHorizontal: 10
  },
  codeContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    marginBottom: 20
  },
  input: {
    width: 50,
    height: 60,
    borderWidth: 1.5,
    borderColor: '#1e90ff',
    borderRadius: 12,
    textAlign: 'center',
    fontSize: 20,
    fontWeight: '600',
    color: '#1e90ff',
    backgroundColor: '#f9f9f9',
    marginHorizontal: 5,
    shadowColor: '#1e90ff',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
    elevation: 2
  },
  button: {
    backgroundColor: '#1e90ff',
    paddingVertical: 14,
    paddingHorizontal: 100,
    borderRadius: 14,
    marginTop: 20,
    shadowColor: '#1e90ff',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 3,
    elevation: 3
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: '600'
  }
});
