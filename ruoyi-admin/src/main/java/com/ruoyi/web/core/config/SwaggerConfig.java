package com.ruoyi.web.core.config;

import com.ruoyi.common.config.RuoYiConfig;
import io.swagger.v3.oas.models.Components;
import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import org.springframework.boot.autoconfigure.condition.ConditionalOnProperty;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/** OpenAPI metadata for explicitly enabled development documentation. */
@Configuration(proxyBeanMethods = false)
public class SwaggerConfig {

    @Bean
    @ConditionalOnProperty(name = "swagger.enabled", havingValue = "true")
    public OpenAPI crmOpenApi(RuoYiConfig config) {
        return new OpenAPI()
                .info(new Info()
                        .title("若依 CRM 接口文档")
                        .version(config.getVersion())
                        .contact(new Contact().name(config.getName())))
                .components(new Components().addSecuritySchemes("Authorization",
                        new SecurityScheme().type(SecurityScheme.Type.HTTP)
                                .scheme("bearer").bearerFormat("JWT")))
                .addSecurityItem(new SecurityRequirement().addList("Authorization"));
    }
}
