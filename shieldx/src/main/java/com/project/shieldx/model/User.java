package com.project.shieldx.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDateTime;
import java.util.UUID;

@Entity
@Table(name = "users")
@Getter
@Setter
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class User {

    @Id
    @GeneratedValue(strategy = GenerationType.UUID)
    private UUID id;

    @Column(nullable = false)
    private String name;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(nullable = false)
    private String password;

    private Long phoneNo;

    @Column(nullable = false)
    private boolean isVerified = false;

    private String profilePicUrl = "";

    private String dateOfBirth;

    @Enumerated(EnumType.STRING)
    @Column(length = 30)
    private Gender gender;

    private String bloodGroup;

    @Column(nullable = false)
    private boolean isSecurityCheckEnabled = true;

    @Embedded
    private DeviceToken deviceToken;

    @Embedded
    private LastLocation lastLocation;

    @OneToOne(mappedBy = "user", cascade = CascadeType.ALL, fetch = FetchType.LAZY)
    private UserSafetyConfig safetyConfig;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false, length = 20)
    private Role role;

    @Column(nullable = false, updatable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    @Column(nullable = false)
    private LocalDateTime updatedAt = LocalDateTime.now();


    @Embeddable
    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class DeviceToken {
        @Column(name = "device_token")
        private String token;        // FCM / Expo / APNS

        @Column(name = "device_token_type")
        private String type;         // "fcm" | "expo" | "apns"

        private LocalDateTime tokenRegisteredAt = LocalDateTime.now();
        private LocalDateTime tokenUpdatedAt = LocalDateTime.now();
    }

    @Embeddable
    @Getter
    @Setter
    @NoArgsConstructor
    @AllArgsConstructor
    @Builder
    public static class LastLocation {
        private Double latitude;
        private Double longitude;
        @Column(name = "location_timestamp")
        private LocalDateTime timestamp;
    }

    public enum Gender {
        MALE,
        FEMALE,
        OTHER,
        PREFER_NOT_TO_SAY
    }

    public enum Role {
        CHILD,
        PARENT
    }
}