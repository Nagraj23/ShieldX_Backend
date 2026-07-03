package com.project.shieldx.DTO;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import java.util.UUID;

@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ConnectionResponseDTO {
    private UUID connectionId; // The unique ID of the link itself
    private UUID parentId;
    private UUID childId;
    private String parentName;
    private String childName;
    private String status;     // PENDING, ACCEPTED, REJECTED
}