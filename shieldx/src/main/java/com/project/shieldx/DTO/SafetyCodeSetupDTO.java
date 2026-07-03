package com.project.shieldx.DTO;

import lombok.Data;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Pattern;

@Data
public class SafetyCodeSetupDTO {

    @NotBlank(message = "Safe PIN cannot be empty")
    @Pattern(regexp = "^\\d{4,6}$", message = "Safe PIN must be 4-6 numeric digits")
    private String safeCode;

    @NotBlank(message = "Duress PIN cannot be empty")
    @Pattern(regexp = "^\\d{4,6}$", message = "Duress PIN must be 4-6 numeric digits")
    private String duressCode;
}