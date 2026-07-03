package com.project.shieldx.controller;

import com.project.shieldx.DTO.ConnectionRequestDTO;
import com.project.shieldx.DTO.ConnectionResponseDTO;
import com.project.shieldx.model.ParentChildConnection;
import com.project.shieldx.service.ParentChildConnectionService;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/connection")
@RequiredArgsConstructor
public class ParentChildConnectionController {

    private final ParentChildConnectionService service;

    // 📌 Send connection request (Child -> Parent via Email lookup)
    @PostMapping("/request")
    public ResponseEntity<String> sendRequest(@RequestBody ConnectionRequestDTO dto) {
        // Fixed the argument bug: passing parentEmail and childId securely
        return ResponseEntity.ok(service.sendConnectionRequestByEmail(dto.getParentEmail(), dto.getChildId()));
    }

    // 📌 Accept or Reject request
    @PostMapping("/respond")
    public ResponseEntity<String> respond(@RequestBody ConnectionResponseDTO dto) {
        // Explicitly map the status string to our model's ConnectionStatus enum type safely
        ParentChildConnection.ConnectionStatus statusEnum = ParentChildConnection.ConnectionStatus.valueOf(dto.getStatus().toUpperCase());
        return ResponseEntity.ok(service.respondToRequest(dto.getConnectionId().toString(), statusEnum));
    }

    // 📌 Get all children linked to a parent
    @GetMapping("/children/{parentId}")
    public ResponseEntity<List<ConnectionResponseDTO>> getChildren(@PathVariable String parentId) {
        return ResponseEntity.ok(service.getChildrenForParent(parentId));
    }

    // 📌 Get all parents linked to a child
    @GetMapping("/parents/{childId}")
    public ResponseEntity<List<ConnectionResponseDTO>> getParents(@PathVariable String childId) {
        return ResponseEntity.ok(service.getParentsForChild(childId));
    }
}