package com.project.shieldx.model;

import jakarta.persistence.*;
import lombok.Data;
import java.util.UUID;


@Data
@Entity
@Table(name = "user_safety_config")
public class UserSafetyConfig {
    @Id
    @GeneratedValue(strategy = GenerationType.AUTO)
    private UUID id;

    @OneToOne
    @JoinColumn(name = "user_id", referencedColumnName = "id", nullable = false)
    private User user;

    @Column(name = "safety_code_hash", nullable = false)
    private String safetyCodeHash;

    @Column(name = "duress_code_hash", nullable = false)
    private String duressCodeHash;
}