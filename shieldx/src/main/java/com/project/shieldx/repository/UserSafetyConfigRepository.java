package com.project.shieldx.repository;

import com.project.shieldx.model.UserSafetyConfig;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;
import java.util.UUID;

public interface UserSafetyConfigRepository extends JpaRepository<UserSafetyConfig, UUID> {
    Optional<UserSafetyConfig> findByUserId(UUID userId);
}