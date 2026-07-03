package com.project.shieldx.DTO;

import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class OtpVerifyRequestDTO {
    private String email;
    private String otp;
}
