package com.project.shieldx.DTO;

import lombok.AllArgsConstructor;
import lombok.Data;

@Data
@AllArgsConstructor
public class SafetyCodeResponseDTO {

    private String safetyCodeHash;
    private String duressCodeHash;
}