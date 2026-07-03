package com.project.shieldx;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.boot.autoconfigure.domain.EntityScan;

@SpringBootApplication // 🚀 Exclude block is completely removed so PostgreSQL auto-configuration activates!
@EnableJpaRepositories(basePackages = "com.project.shieldx.repository") // Explicitly boots up relational JPA repositories
@EntityScan(basePackages = "com.project.shieldx.model") // Explicitly tells Hibernate where your relational @Entity classes live
public class ShieldxApplication {

	public static void main(String[] args) {
		SpringApplication.run(ShieldxApplication.class, args);
	}
}