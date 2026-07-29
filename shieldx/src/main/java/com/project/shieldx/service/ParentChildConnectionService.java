package com.project.shieldx.service;

import com.project.shieldx.DTO.ConnectionResponseDTO;
import com.project.shieldx.model.ParentChildConnection;
import com.project.shieldx.model.User;
import com.project.shieldx.repository.ParentChildConnectionRepo;
import com.project.shieldx.repository.UserRepo;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ParentChildConnectionService {

    private final ParentChildConnectionRepo repo;
    private final UserRepo userRepo;
    private final RestTemplate restTemplate;

    // FastAPI Notification Microservice Endpoint
    private static final String NOTIFICATION_SERVICE_URL = "http://10.164.144.154:8001/api/v1/notifications/send";

    // 📌 Send request (Only CHILD can send request to PARENT using EMAIL)
    @Transactional
    public String sendConnectionRequestByEmail(String parentEmail, String childIdStr) {
        System.out.println("📌 [CONN REQUEST] START | Parent Email: " + parentEmail + " | Child ID: " + childIdStr);

        // Convert incoming String ID to native UUID
        UUID childId = UUID.fromString(childIdStr);

        // Validate child entity existence
        User childUser = userRepo.findById(childId)
                .orElseThrow(() -> new RuntimeException("Child user not found 💀"));

        // Enforce strict business role checks
        if (childUser.getRole() != User.Role.CHILD) {
            throw new RuntimeException("Only CHILD users can send connection requests! ❌");
        }

        // Validate parent target existence by EMAIL and ROLE
        User parentUser = userRepo.findByEmailAndRole(parentEmail, User.Role.PARENT)
                .orElseThrow(() -> new RuntimeException("Parent account matching that email not found 😵"));

        // Prevent duplicate requests using direct object evaluation criteria
        if (repo.findByParentAndChild(parentUser, childUser).isPresent()) {
            return "Connection request already exists! ⚠️";
        }

        // Persist clean relational link mapping with explicit foreign bindings
        ParentChildConnection connection = ParentChildConnection.builder()
                .parent(parentUser)
                .child(childUser)
                .status(ParentChildConnection.ConnectionStatus.PENDING)
                .createdAt(LocalDateTime.now())
                .updatedAt(LocalDateTime.now())
                .build();

        ParentChildConnection savedConnection = repo.save(connection);
        System.out.println("✅ [CONN REQUEST] SUCCESS | Pending record saved to PostgreSQL.");

        // 🔔 Dispatch Real-Time Push Notification to FastAPI Notification Engine (Port 8001)
        dispatchPairingNotification(childUser, parentUser, savedConnection.getId().toString());

        return "Connection request sent! 🔐";
    }

    // 📌 Helper Method: Non-blocking Notification Dispatch
    private void dispatchPairingNotification(User childUser, User parentUser, String connectionId) {
        try {
            Map<String, Object> notificationPayload = new HashMap<>();

            // 🆔 1. ADD THIS LINE (Generates UUID for notification_id):
            notificationPayload.put("notification_id", UUID.randomUUID().toString());

            // Sender Information
            notificationPayload.put("sender", Map.of(
                    "id", childUser.getId().toString(),
                    "type", "USER",
                    "name", childUser.getName() != null ? childUser.getName() : "Child Device"
            ));

            // Target Parent Recipient
            notificationPayload.put("recipients", List.of(Map.of(
                    "id", parentUser.getId().toString(),
                    "type", "USER",
                    "status", "PENDING"
            )));

            // Alert Content
            notificationPayload.put("notification", Map.of(
                    "type", "PAIRING_REQUEST",
                    "category", "PAIRING",
                    "priority", "HIGH",
                    "title", "New Child Pairing Request",
                    "body", (childUser.getName() != null ? childUser.getName() : "Child") + " requested to connect their device."
            ));

            // Custom Payload
            notificationPayload.put("payload", Map.of(
                    "target_screen", "AcceptInvitationScreen",
                    "connectionId", connectionId,
                    "childId", childUser.getId().toString(),
                    "childName", childUser.getName() != null ? childUser.getName() : "Child",
                    "pairCode", "SHIELD-" + (1000 + new Random().nextInt(9000))
            ));

            // Execute HTTP POST to FastAPI
            restTemplate.postForEntity(NOTIFICATION_SERVICE_URL, notificationPayload, Map.class);
            System.out.println("🚀 [CONN REQUEST] Dispatch sent to Notification Engine for Parent UUID: " + parentUser.getId());

        } catch (Exception e) {
            System.err.println("⚠️ [CONN REQUEST] Notification Service dispatch failed: " + e.getMessage());
        }
    }

    // 📌 Respond to request (PARENT accepts / rejects)
    @Transactional
    public String respondToRequest(String connectionIdStr, ParentChildConnection.ConnectionStatus status) {
        System.out.println("📌 [CONN RESPOND] START | Connection ID: " + connectionIdStr + " | Status: " + status);

        UUID connectionId = UUID.fromString(connectionIdStr);
        ParentChildConnection connection = repo.findById(connectionId)
                .orElseThrow(() -> new RuntimeException("Connection record not found 💀"));

        // Update the lifecycle status of the link directly
        connection.setStatus(status);
        connection.setUpdatedAt(LocalDateTime.now());
        repo.save(connection);

        System.out.println("✅ [CONN RESPOND] SUCCESS | Relationship marked as " + status);

        return status == ParentChildConnection.ConnectionStatus.ACCEPTED
                ? "Connection accepted! 🚀"
                : "Connection rejected! ❌";
    }

    // 📌 Get children for a parent
    @Transactional(readOnly = true)
    public List<ConnectionResponseDTO> getChildrenForParent(String parentIdStr) {
        UUID parentId = UUID.fromString(parentIdStr);
        User parent = userRepo.findById(parentId)
                .orElseThrow(() -> new RuntimeException("Parent user not found"));

        return repo.findByParent(parent)
                .stream()
                .map(conn -> ConnectionResponseDTO.builder()
                        .connectionId(conn.getId())
                        .parentId(conn.getParent().getId())
                        .childId(conn.getChild().getId())
                        .parentName(conn.getParent().getName())
                        .childName(conn.getChild().getName())
                        .status(conn.getStatus().name())
                        .build())
                .collect(Collectors.toList());
    }

    // 📌 Get parents for a child
    @Transactional(readOnly = true)
    public List<ConnectionResponseDTO> getParentsForChild(String childIdStr) {
        UUID childId = UUID.fromString(childIdStr);
        User child = userRepo.findById(childId)
                .orElseThrow(() -> new RuntimeException("Child user not found"));

        return repo.findByChild(child)
                .stream()
                .map(conn -> ConnectionResponseDTO.builder()
                        .connectionId(conn.getId())
                        .parentId(conn.getParent().getId())
                        .childId(conn.getChild().getId())
                        .parentName(conn.getParent().getName())
                        .childName(conn.getChild().getName())
                        .status(conn.getStatus().name())
                        .build())
                .collect(Collectors.toList());
    }
}