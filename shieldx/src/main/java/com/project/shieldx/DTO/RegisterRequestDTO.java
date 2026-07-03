package com.project.shieldx.DTO;

import com.project.shieldx.model.User;
import com.project.shieldx.model.User.Role;
import lombok.*;

import java.time.LocalDate;

@Getter @Setter
@NoArgsConstructor @AllArgsConstructor
public class RegisterRequestDTO {
    private String name;
    private String email;
    private String password;
    private Long phoneNo;
    private Role role;



}
