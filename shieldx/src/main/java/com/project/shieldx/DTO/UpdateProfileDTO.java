package com.project.shieldx.DTO;

import com.project.shieldx.model.User.Gender;
import lombok.*;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class UpdateProfileDTO {
    private String name;
    private Long phoneNo;
    private String dateOfBirth;
    private Gender gender;
    private String bloodGroup;
    private String profilePicUrl;
}
