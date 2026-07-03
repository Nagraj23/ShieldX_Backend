package com.project.shieldx.service;

import com.project.shieldx.DTO.SafetyCodeResponseDTO;
import com.project.shieldx.DTO.SafetyCodeSetupDTO;
import com.project.shieldx.model.User;
import com.project.shieldx.model.UserSafetyConfig;
import com.project.shieldx.repository.UserRepo;
import com.project.shieldx.repository.UserSafetyConfigRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import java.util.UUID;

@Service
@RequiredArgsConstructor
public class SafetyConfigService {

    private final UserSafetyConfigRepository safetyConfigRepository;
    private final UserRepo userRepository;
    private final PasswordEncoder passwordEncoder;

    @Transactional
    public void userConfig(UUID user , SafetyCodeSetupDTO safe){

        if (safe.getSafeCode().equals(safe.getDuressCode())) {
            throw new IllegalArgumentException("Safe PIN and Duress PIN cannot be identical!");
        }

        User exist = userRepository.findById(user)
                .orElseThrow(() -> new RuntimeException("User not found with ID: " + user));

        UserSafetyConfig config = safetyConfigRepository.findByUserId(user)
                .orElse(new UserSafetyConfig());

        config.setUser(exist);
        config.setSafetyCodeHash(passwordEncoder.encode(safe.getSafeCode()));
        config.setDuressCodeHash(passwordEncoder.encode(safe.getDuressCode()));

        safetyConfigRepository.save(config);
    }

    public SafetyCodeResponseDTO getSafetyCodes(UUID userId) {

    UserSafetyConfig config = safetyConfigRepository.findByUserId(userId)
            .orElseThrow(() -> new RuntimeException("Safety configuration not found"));

    return new SafetyCodeResponseDTO(
            config.getSafetyCodeHash(),
            config.getDuressCodeHash()
    );
}
}
