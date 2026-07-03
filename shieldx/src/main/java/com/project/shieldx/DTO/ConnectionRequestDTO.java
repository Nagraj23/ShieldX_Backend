package com.project.shieldx.DTO;

import lombok.Data;

@Data
public class ConnectionRequestDTO {
    private String childId;     // Passed as a String to easily match incoming requests
    private String parentEmail; // Changed from parentId to match your email search flow!
}