package com.project.shieldx.controller;

import com.project.shieldx.DTO.*;
import com.project.shieldx.model.User;
import com.project.shieldx.service.AuthService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import com.project.shieldx.service.SafetyConfigService;

import java.util.UUID;

@RestController
@RequestMapping("/api/auth")
@RequiredArgsConstructor
public class AuthController {

    private final AuthService authService;
    private final SafetyConfigService safetyService;

    @PostMapping("/safe/{userId}")
    public ResponseEntity<String> safety(@PathVariable UUID userId, @RequestBody SafetyCodeSetupDTO dto) {
        safetyService.userConfig(userId, dto);
        return ResponseEntity.ok("Safety configuration initialized successfully.");
    }

    @GetMapping("/safe/{userId}")
        public ResponseEntity<SafetyCodeResponseDTO> getSafetyCodes(@PathVariable UUID userId) {
        return ResponseEntity.ok(safetyService.getSafetyCodes(userId));
    }

    @PostMapping("/register")
    public ResponseEntity<String> register(@RequestBody RegisterRequestDTO request) {
        return ResponseEntity.ok(authService.register(request));
    }

    @PostMapping("/login")
    public ResponseEntity<AuthResponseDTO> login(@RequestBody LoginRequestDTO request) {
        return ResponseEntity.ok(authService.login(request));
    }


    @PostMapping("/verify-otp")
    public ResponseEntity<String> verifyOtp(@RequestBody OtpVerifyRequestDTO otpReq) {
        String result = authService.verifyOtp(otpReq.getEmail(), otpReq.getOtp());
        return ResponseEntity.ok(result);
    }

    @PutMapping("/update-profile/{userId}")
    public ResponseEntity<String> updateProfile(@PathVariable UUID userId, @RequestBody UpdateProfileDTO dto) {
        return ResponseEntity.ok(authService.updateProfile(userId, dto));
    }

    @PostMapping("/resend")
    public ResponseEntity<String> resendOtp(@RequestBody Resend dto) {
        return ResponseEntity.ok(authService.resendOtp(dto.getEmail()));
    }

    @GetMapping("/user/{id}")
    public ResponseEntity<User> getUserById(@PathVariable UUID id) {
        return ResponseEntity.ok(authService.getUserById(id));
    }

    @PostMapping("/forgot-password")
    public ResponseEntity<String> forgotPassword(@RequestBody ForgotPasswordRequestDTO request) {
        return ResponseEntity.ok(authService.forgotPassword(request.getEmail()));
    }

    @PostMapping("/reset-password")
    public ResponseEntity<String> resetPassword(@RequestBody ResetPasswordDTO request) {
        return ResponseEntity.ok(authService.resetPassword(request));
    }
}