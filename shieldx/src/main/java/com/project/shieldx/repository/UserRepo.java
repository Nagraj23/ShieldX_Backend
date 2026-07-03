package com.project.shieldx.repository;

import com.project.shieldx.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;
import java.util.UUID;

@Repository
public interface UserRepo extends JpaRepository<User, UUID> {

    // Spring Data JPA automatically derives SQL B-Tree index scans for unique columns
    Optional<User> findByEmail(String email);

    boolean existsByEmail(String email);

    // Filter signatures updated to use the native User.Role enum structure
    Optional<User> findByEmailAndRole(String email, User.Role role);
}