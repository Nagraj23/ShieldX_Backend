package com.project.shieldx.util;

import org.springframework.stereotype.Component;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

@Component
public class OtpStore {

    // Internal POJO to encapsulate OTP details
    public static class OtpDetails {
        private final String otp;
        private final long expiresAt;

        public OtpDetails(String otp, long expiresAt) {
            this.otp = otp;
            this.expiresAt = expiresAt;
        }

        public String getOtp() { return otp; }
        public long getExpiresAt() { return expiresAt; }
    }

    // Thread-safe concurrent map designed for high-concurrency access
    private final Map<String, OtpDetails> otpMap = new ConcurrentHashMap<>();

    /**
     * Stores an OTP for an email address with a defined validity duration.
     */
    public void storeOtp(String email, String otp, long expiryMillis) {
        long absoluteExpiry = System.currentTimeMillis() + expiryMillis;
        otpMap.put(email, new OtpDetails(otp, absoluteExpiry));
    }

    /**
     * Validates the input OTP and cleans up the memory footprint automatically.
     */
    public boolean verifyOtp(String email, String inputOtp) {
        OtpDetails details = otpMap.get(email);
        
        if (details == null) {
            return false;
        }

        // Check if the current time has bypassed our absolute expiration window
        if (System.currentTimeMillis() > details.getExpiresAt()) {
            otpMap.remove(email); // Purge stale data
            return false;
        }

        boolean match = details.getOtp().equals(inputOtp);
        if (match) {
            otpMap.remove(email); // Evict from RAM upon successful validation
        }
        
        return match;
    }
}