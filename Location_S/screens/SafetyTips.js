import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TextInput,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Modal,
  TouchableOpacity,
  Platform,
  ActivityIndicator
} from 'react-native';

// Define the base URL for your API
const API_BASE_URL = 'http://192.168.174.136:8000'; // Replace with your actual server IP/port

export default function SafetyTips() {
  const [messages, setMessages] = useState([
    { id: '0', type: 'bot', text: 'Welcome to ShieldX! Your personal safety assistant. How can I assist you today?' }
  ]);
  const [input, setInput] = useState('');
  const [securityCheckVisible, setSecurityCheckVisible] = useState(false);
  const [securityCode, setSecurityCode] = useState('');
  const [securityCheckTimer, setSecurityCheckTimer] = useState(60);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const timerRef = useRef(null);
  const checkIntervalRef = useRef(null);
  const flatListRef = useRef(null);
  const oneHourTimerRef = useRef(null);

  useEffect(() => {
    checkIntervalRef.current = setInterval(() => {
      checkForSecurityRequests();
    }, 30000);
    checkForSecurityRequests();

    return () => {
      if (checkIntervalRef.current) clearInterval(checkIntervalRef.current);
      if (timerRef.current) clearInterval(timerRef.current);
      if (oneHourTimerRef.current) clearTimeout(oneHourTimerRef.current);
    };
  }, []);

  useEffect(() => {
    if (flatListRef.current && messages.length > 0) {
      flatListRef.current.scrollToEnd({ animated: true });
    }
  }, [messages]);

  // Start or reset the 1-hour timer to trigger security check again
  const startOneHourTimer = () => {
    if (oneHourTimerRef.current) {
      clearTimeout(oneHourTimerRef.current);
    }
    oneHourTimerRef.current = setTimeout(() => {
      triggerSecurityCheck();
    }, 3600000); // 1 hour in milliseconds
  };

  const checkForSecurityRequests = async () => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/security-check-status`);
      const data = await res.json();

      if (data && data.pending) {
        if (!securityCheckVisible) {
          setSecurityCheckVisible(true);
          startSecurityTimer();
          startOneHourTimer();

          setMessages(prev => [...prev, {
            id: Date.now().toString() + '_bot',
            type: 'bot',
            text: '🔐 Security check required. Please enter your security code.'
          }]);
        }
      }
    } catch (error) {
      console.error('Error checking security status:', error);
    }
  };

  const startSecurityTimer = () => {
    setSecurityCheckTimer(60);

    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    timerRef.current = setInterval(() => {
      setSecurityCheckTimer(prev => {
        if (prev <= 1) {
          clearInterval(timerRef.current);
          setSecurityCheckVisible(false);

          setMessages(prev => [...prev, {
            id: Date.now().toString() + '_bot',
            type: 'bot',
            text: '🚨 Security check timeout! SOS alert has been triggered.'
          }]);
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const submitSecurityCode = async () => {
    if (!securityCode.trim()) return;

    setIsSubmitting(true);

    try {
      // Fixed endpoint to match your backend implementation
      const res = await fetch(`${API_BASE_URL}/security-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code: securityCode })
      });
      const data = await res.json();

      clearInterval(timerRef.current);
      setSecurityCheckVisible(false);

      setMessages(prev => [...prev, {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: data.status === 'success'
          ? `✅ ${data.message}`
          : `🚨 ${data.message}`
      }]);

      // Reset the 1-hour timer on successful or failed submission
      startOneHourTimer();

    } catch (error) {
      console.error('Error submitting security code:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: '❌ Error processing security check. Please try again.'
      }]);
    } finally {
      setIsSubmitting(false);
      setSecurityCode('');
      setSecurityCheckVisible(false);
    }
  };

  const cancelSecurityCheck = () => {
    clearInterval(timerRef.current);
    setSecurityCheckVisible(false);

    setMessages(prev => [...prev, {
      id: Date.now().toString() + '_bot',
      type: 'bot',
      text: '🚨 Security check canceled! SOS alert has been triggered.'
    }]);
    setSecurityCode('');
  };

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMsg = { id: Date.now().toString(), type: 'user', text: input };
    setMessages((prev) => [...prev, userMsg]);
    const currentInput = input;
    setInput('');

    try {
      const res = await fetch(`${API_BASE_URL}/api/gemma`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt: currentInput })
      });
      const data = await res.json();

      const botMsg = {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: data.reply || 'Sorry, I could not generate a response.'
      };
      setMessages((prev) => [...prev, botMsg]);
    } catch (error) {
      console.error('Error sending message:', error);
      setMessages((prev) => [...prev, {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: 'Error connecting to the safety assistant.'
      }]);
    }
  };

  const triggerSecurityCheck = async () => {
    try {
      await fetch(`${API_BASE_URL}/api/trigger-security-check`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' }
      });

      setSecurityCheckVisible(true);
      startSecurityTimer();
      startOneHourTimer();

      setMessages(prev => [...prev, {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: '🔐 Security check initiated. Please enter your security code.'
      }]);
    } catch (error) {
      console.error('Error triggering security check:', error);
      setMessages(prev => [...prev, {
        id: Date.now().toString() + '_bot',
        type: 'bot',
        text: '❌ Error initiating security check.'
      }]);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={Platform.OS === 'ios' ? 90 : 0}
    >
      <View style={styles.introContainer}>
        <Text style={styles.introText}>Welcome to ShieldX: Your Personal Safety Assistant</Text>
      </View>

      <FlatList
        ref={flatListRef}
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View style={[
            styles.message,
            item.type === 'user' ? styles.user : styles.bot,
            styles.bubbleShadow
          ]}>
            <Text style={[
              styles.text,
              item.type === 'user' ? styles.userText : styles.botText
            ]}>
              {item.text}
            </Text>
          </View>
        )}
        contentContainerStyle={styles.messagesContainer}
        onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
      />

      <View style={styles.inputContainer}>
        <TextInput
          value={input}
          onChangeText={setInput}
          style={styles.input}
          placeholder="Describe your safety concern..."
          placeholderTextColor="#aaa"
          multiline={true}
          maxLength={500}
        />
        <TouchableOpacity
          style={styles.sendButtonWrapper}
          onPress={sendMessage}
          disabled={!input.trim()}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity style={styles.debugButton} onPress={triggerSecurityCheck}>
        <Text style={styles.debugButtonText}>Test Security Check</Text>
      </TouchableOpacity>

      <Modal
        visible={securityCheckVisible}
        transparent={true}
        animationType="slide"
        onRequestClose={cancelSecurityCheck}
      >
        <View style={styles.modalContainer}>
          <View style={styles.modalContent}>
            <Text style={styles.modalTitle}>🔐 Security Check</Text>
            <Text style={styles.modalText}>
              Please enter your security code to verify your safety.
            </Text>
            <Text style={[
              styles.timerText,
              securityCheckTimer <= 10 ? styles.timerWarning : null
            ]}>
              Time remaining: {securityCheckTimer} seconds
            </Text>
            <TextInput
              value={securityCode}
              onChangeText={setSecurityCode}
              style={styles.securityInput}
              placeholder="Enter security code"
              keyboardType="numeric"
              maxLength={4}
              autoFocus={true}
              editable={!isSubmitting}
            />
            <View style={styles.modalButtonContainer}>
              {isSubmitting ? (
                <ActivityIndicator size="small" color="#4F8EF7" />
              ) : (
                <>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.submitButton]}
                    onPress={submitSecurityCode}
                    disabled={!securityCode.trim()}
                  >
                    <Text style={styles.buttonText}>Submit</Text>
                  </TouchableOpacity>
                  <TouchableOpacity
                    style={[styles.modalButton, styles.cancelButton]}
                    onPress={cancelSecurityCheck}
                  >
                    <Text style={styles.buttonText}>Cancel (Trigger SOS)</Text>
                  </TouchableOpacity>
                </>
              )}
            </View>
          </View>
        </View>
      </Modal>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  // Styles remain the same as before
  container: {
    flex: 1,
    backgroundColor: '#f7f9fa',
    padding: 10,
  },
  introContainer: {
    backgroundColor: '#4F8EF7',
    borderRadius: 12,
    paddingVertical: 12,
    paddingHorizontal: 20,
    marginBottom: 12,
    alignItems: 'center',
    marginTop: 20,
  },
  shieldLogo: {
    width: 60,
    height: 60,
    marginBottom: 10,
  },
  introText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
    textAlign: 'center',
  },
  messagesContainer: {
    paddingBottom: 10,
  },
  message: {
    marginVertical: 6,
    paddingVertical: 12,
    paddingHorizontal: 18,
    borderRadius: 22,
    maxWidth: '80%',
    minWidth: 60,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 4,
    elevation: 2,
  },
  bubbleShadow: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.10,
    shadowRadius: 6,
    elevation: 3,
  },
  user: {
    alignSelf: 'flex-end',
    backgroundColor: '#4F8EF7',
  },
  bot: {
    alignSelf: 'flex-start',
    backgroundColor: '#e6eaf3',
  },
  text: {
    fontSize: 16,
  },
  userText: {
    color: '#fff',
  },
  botText: {
    color: '#222',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 10,
    borderTopWidth: 1,
    borderColor: '#e0e0e0',
    alignItems: 'center',
    backgroundColor: '#fff',
    borderRadius: 18,
    marginTop: 4,
    marginBottom: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.07,
    shadowRadius: 2,
    elevation: 1,
  },
  input: {
    flex: 1,
    backgroundColor: '#f2f4f8',
    borderRadius: 20,
    paddingHorizontal: 15,
    paddingVertical: 10,
    fontSize: 16,
    marginRight: 8,
    color: '#222',
    borderWidth: 1,
    borderColor: '#e0e0e0',
    maxHeight: 100,
  },
  sendButtonWrapper: {
    borderRadius: 20,
    overflow: 'hidden',
    backgroundColor: '#4F8EF7',
    elevation: 2,
    paddingHorizontal: 16,
    paddingVertical: 10,
  },
  sendButtonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },

  // Modal styles
  modalContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(0,0,0,0.5)',
  },
  modalContent: {
    width: '85%',
    backgroundColor: 'white',
    borderRadius: 20,
    padding: 25,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: {
      width: 0,
      height: 2,
    },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  modalTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 15,
    color: '#4F8EF7',
  },
  modalText: {
    fontSize: 16,
    marginBottom: 15,
    textAlign: 'center',
    color: '#333',
    lineHeight: 22,
  },
  timerText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
    marginBottom: 20,
  },
  timerWarning: {
    color: '#FF3B30',
  },
  securityInput: {
    width: '100%',
    height: 60,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 10,
    paddingHorizontal: 15,
    fontSize: 24,
    marginBottom: 25,
    textAlign: 'center',
    letterSpacing: 10,
    fontWeight: 'bold',
  },
  modalButtonContainer: {
    width: '100%',
    alignItems: 'center',
  },
  modalButton: {
    width: '100%',
    padding: 15,
    borderRadius: 10,
    alignItems: 'center',
    marginBottom: 10,
  },
  submitButton: {
    backgroundColor: '#4F8EF7',
  },
  cancelButton: {
    backgroundColor: '#FF3B30',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  debugButton: {
    backgroundColor: '#ddd',
    padding: 10,
    borderRadius: 10,
    marginTop: 10,
    alignItems: 'center',
  },
  debugButtonText: {
    color: '#333',
  },
});
