package com.project.shieldx.model;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class OTP {
    private String otp;
    private long expiryTime;
}
