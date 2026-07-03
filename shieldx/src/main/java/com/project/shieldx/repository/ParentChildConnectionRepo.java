package com.project.shieldx.repository;

import com.project.shieldx.model.ParentChildConnection;
import com.project.shieldx.model.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;
import java.util.UUID;

@Repository
public interface ParentChildConnectionRepo extends JpaRepository<ParentChildConnection, UUID> {

    // Upgraded from findByParentId(String) to query straight across the Foreign Key object link
    List<ParentChildConnection> findByParent(User parent);

    // Upgraded from findByChildId(String) to query straight across the Foreign Key object link
    List<ParentChildConnection> findByChild(User child);

    // Atomic unique combination lookup using the direct object properties
    Optional<ParentChildConnection> findByParentAndChild(User parent, User child);
}