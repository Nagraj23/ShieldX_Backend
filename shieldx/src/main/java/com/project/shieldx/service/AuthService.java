package com.project.shieldx.service;

import com.project.shieldx.DTO.*;
import com.project.shieldx.model.User;
import com.project.shieldx.repository.UserRepo;
import com.project.shieldx.security.JWTService;
import com.project.shieldx.util.OtpStore;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Service
@RequiredArgsConstructor
public class AuthService {

    private final UserRepo repo;
    private final PasswordEncoder encoder;
    private final JWTService jwtService;
    private final EmailService emailService;
    private final OtpStore otpStore;

    // 🚀 REGISTER
    public String register(RegisterRequestDTO req) {
        System.out.println("🚀 [REGISTER] START | Email: " + req.getEmail());

        if (repo.existsByEmail(req.getEmail())) {
            System.out.println("❌ [REGISTER] FAIL | Email already exists: " + req.getEmail());
            throw new RuntimeException("Email already exists 💀");
        }

        // Mapping directly to the updated PostgreSQL model using standard Enums
        User user = User.builder()
                .name(req.getName())
                .email(req.getEmail())
                .password(encoder.encode(req.getPassword()))
                .role(req.getRole()) // Implicitly mapped from DTO parameter
                .isVerified(false)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        repo.save(user);
        System.out.println("✅ [REGISTER] USER SAVED | ID: " + user.getId());

        String otp = generateOtp();
        // 24 hours converted to long primitive milliseconds
        otpStore.storeOtp(req.getEmail(), otp, 24L * 60 * 60 * 1000);
        System.out.println("🔐 [REGISTER] OTP GENERATED for " + req.getEmail());

        emailService.sendOtpEmail(
                user.getEmail(),
                "ShieldX Email Verification OTP",
                user.getName(),
                otp
        );

        System.out.println("📧 [REGISTER] OTP EMAIL SENT to " + req.getEmail());
        System.out.println("🏁 [REGISTER] END | " + req.getEmail());

        return "User registered. OTP sent 🔐";
    }

    // 🔐 VERIFY OTP
    public String verifyOtp(String email, String otpInput) {
        System.out.println("🔐 [VERIFY OTP] START | Email: " + email);

        // Atomic multi-thread check via our centralized in-memory component
        boolean isOtpValid = otpStore.verifyOtp(email, otpInput);

        if (!isOtpValid) {
            System.out.println("❌ [VERIFY OTP] FAIL | Invalid, expired, or non-existent token for: " + email);
            return "Invalid or expired OTP ❌";
        }

        User user = repo.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("User not found"));

        user.setVerified(true);
        user.setUpdatedAt(LocalDateTime.now());
        repo.save(user);

        System.out.println("✅ [VERIFY OTP] SUCCESS | Email verified");
        return "OTP verified 🚀";
    }

    // ✅ LOGIN
    public AuthResponseDTO login(LoginRequestDTO req) {
        System.out.println("✅ [LOGIN] START | Email: " + req.getEmail());

        User user = repo.findByEmail(req.getEmail())
                .orElseThrow(() -> {
                    System.out.println("❌ [LOGIN] FAIL | Email not found");
                    return new RuntimeException("Invalid email or password ❌");
                });

        if (!user.isVerified()) {
            System.out.println("⚠️ [LOGIN] FAIL | Email not verified");
            throw new RuntimeException("Email not verified yet ⚠️");
        }

        if (!encoder.matches(req.getPassword(), user.getPassword())) {
            System.out.println("❌ [LOGIN] FAIL | Wrong password");
            throw new RuntimeException("Invalid email or password ❌");
        }

        String jwt = jwtService.generateToken(user.getEmail());
        System.out.println("🎉 [LOGIN] SUCCESS | JWT issued for " + req.getEmail());

        // Returns user.getId() directly as a UUID instance inside our updated contract DTO
        return new AuthResponseDTO(jwt, user.getId(), user.getName());
    }

    // 🔥 FORGOT PASSWORD
    public String forgotPassword(String email) {
        System.out.println("🔥 [FORGOT PASSWORD] START | Email: " + email);

        User user = repo.findByEmail(email)
                .orElseThrow(() -> {
                    System.out.println("❌ [FORGOT PASSWORD] FAIL | Email not found");
                    return new RuntimeException("User not found 💀");
                });

        String otp = generateOtp();
        otpStore.storeOtp(email, otp, 24L * 60 * 60 * 1000);
        System.out.println("🔐 [FORGOT PASSWORD] OTP GENERATED");

        emailService.sendOtpEmail(
                email,
                "ShieldX Password Reset OTP",
                user.getName(),
                otp
        );

        System.out.println("📧 [FORGOT PASSWORD] OTP EMAIL SENT");
        return "OTP sent for password reset 🔥";
    }

    // ⚒️ UPDATE PROFILE
    public String updateProfile(UUID userId, UpdateProfileDTO dto) {
        System.out.println("⚒️ [UPDATE PROFILE] START | UserID: " + userId);

        // Parameter type safely modified from String to UUID
        User user = repo.findById(userId)
                .orElseThrow(() -> {
                    System.out.println("❌ [UPDATE PROFILE] FAIL | User not found");
                    return new RuntimeException("User not found 💀");
                });

        user.setName(dto.getName());
        user.setPhoneNo(dto.getPhoneNo());
        user.setGender(dto.getGender());
        user.setDateOfBirth(dto.getDateOfBirth());
        user.setBloodGroup(dto.getBloodGroup());
        user.setProfilePicUrl(dto.getProfilePicUrl());
        user.setUpdatedAt(LocalDateTime.now());

        repo.save(user);
        System.out.println("✅ [UPDATE PROFILE] SUCCESS | UserID: " + userId);

        return "Profile updated successfully ✨";
    }

    // 🔍 GET USER BY ID
    public User getUserById(UUID id) {
        System.out.println("🔍 [GET USER] START | ID: " + id);

        // Parameter type safely modified from String to UUID
        User user = repo.findById(id)
                .orElseThrow(() -> {
                    System.out.println("❌ [GET USER] FAIL | User not found");
                    return new RuntimeException("User not found 😵");
                });

        System.out.println("✅ [GET USER] SUCCESS | Email: " + user.getEmail());
        return user;
    }

    // 🔄 RESEND OTP
    public String resendOtp(String email) {
        System.out.println("🔄 [RESEND OTP] START | Email: " + email);

        User user = repo.findByEmail(email)
                .orElseThrow(() -> {
                    System.out.println("❌ [RESEND OTP] FAIL | User not found");
                    return new RuntimeException("User not found 💀");
                });

        if (user.isVerified()) {
            System.out.println("⚠️ [RESEND OTP] FAIL | User already verified");
            return "User is already verified ✅";
        }

        String otp = generateOtp();

        // Store OTP for 24 hours
        otpStore.storeOtp(email, otp, 24L * 60 * 60 * 1000);

        System.out.println("🔐 [RESEND OTP] NEW OTP GENERATED");

        emailService.sendOtpEmail(
                email,
                "ShieldX Email Verification OTP",
                user.getName(),
                otp
        );

        System.out.println("📧 [RESEND OTP] EMAIL SENT");

        return "New OTP sent successfully 🚀";
    }

    // 🔓 RESET PASSWORD
    public String resetPassword(ResetPasswordDTO dto) {
        System.out.println("🔓 [RESET PASSWORD] START | Email: " + dto.getEmail());

        User user = repo.findByEmail(dto.getEmail())
                .orElseThrow(() -> {
                    System.out.println("❌ [RESET PASSWORD] FAIL | Email not found");
                    return new RuntimeException("User not found");
                });

        user.setPassword(encoder.encode(dto.getNewPassword()));
        user.setUpdatedAt(LocalDateTime.now());
        repo.save(user);

        System.out.println("✅ [RESET PASSWORD] SUCCESS | Password updated");
        return "Password reset successful 🔓";
    }

    // 🎲 OTP GENERATOR
    private String generateOtp() {
        return String.format("%06d", new Random().nextInt(999999));
    }
}