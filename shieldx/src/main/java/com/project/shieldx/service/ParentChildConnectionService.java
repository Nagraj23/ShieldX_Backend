package com.project.shieldx.service;

import com.project.shieldx.DTO.ConnectionResponseDTO;
import com.project.shieldx.model.ParentChildConnection;
import com.project.shieldx.model.User;
import com.project.shieldx.repository.ParentChildConnectionRepo;
import com.project.shieldx.repository.UserRepo;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class ParentChildConnectionService {

    private final ParentChildConnectionRepo repo;
    private final UserRepo userRepo;

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

        repo.save(connection);
        System.out.println("✅ [CONN REQUEST] SUCCESS | Pending record saved.");
        return "Connection request sent! 🔐";
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

        // NOTE: We no longer manually update loose arrays inside User objects!
        // The relational link itself represents the source of truth dynamically.
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

        // Query the relational index matrix mapping straight across the parent object filter
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

        // Query the relational index matrix mapping straight across the child object filter
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