package com.project.shieldx;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.data.jpa.repository.config.EnableJpaRepositories;
import org.springframework.web.client.RestTemplate;
import org.springframework.boot.autoconfigure.domain.EntityScan;
import org.springframework.context.annotation.Bean;

@SpringBootApplication // 🚀 Exclude block is completely removed so PostgreSQL auto-configuration activates!
@EnableJpaRepositories(basePackages = "com.project.shieldx.repository") // Explicitly boots up relational JPA repositories
@EntityScan(basePackages = "com.project.shieldx.model") // Explicitly tells Hibernate where your relational @Entity classes live
public class ShieldxApplication {

	public static void main(String[] args) {
		SpringApplication.run(ShieldxApplication.class, args);
	}

	@Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}