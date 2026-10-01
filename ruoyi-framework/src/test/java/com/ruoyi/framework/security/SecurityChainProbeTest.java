package com.ruoyi.framework.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.mockito.Mockito.mock;

import com.ruoyi.framework.config.SecurityConfig;
import com.ruoyi.framework.security.filter.JwtAuthenticationTokenFilter;
import com.ruoyi.framework.security.handle.AuthenticationEntryPointImpl;
import com.ruoyi.framework.security.handle.LogoutSuccessHandlerImpl;
import com.ruoyi.framework.web.service.TokenService;
import com.ruoyi.common.core.redis.RedisCache;
import jakarta.servlet.Filter;
import jakarta.servlet.http.Cookie;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.ResponseEntity;
import org.springframework.data.redis.core.RedisTemplate;
import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.test.context.junit.jupiter.web.SpringJUnitWebConfig;
import org.springframework.test.context.TestPropertySource;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.test.web.servlet.MockMvc;
import org.springframework.test.web.servlet.setup.MockMvcBuilders;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.context.WebApplicationContext;
import org.springframework.web.servlet.config.annotation.EnableWebMvc;

@SpringJUnitWebConfig(classes = SecurityChainProbeTest.TestConfig.class)
@TestPropertySource(properties = {"token.header=Authorization", "token.expireTime=30"})
class SecurityChainProbeTest
{
    @org.springframework.test.context.DynamicPropertySource
    static void tokenSecret(org.springframework.test.context.DynamicPropertyRegistry registry)
    {
        registry.add("token.secret", () -> java.util.Base64.getEncoder().encodeToString(new byte[64]));
    }
    @Autowired
    private WebApplicationContext context;

    private MockMvc mvc;

    @BeforeEach
    void setUp()
    {
        mvc = MockMvcBuilders.webAppContextSetup(context)
                .addFilters(context.getBean("springSecurityFilterChain", Filter.class)).build();
    }

    @Test
    void onlyGetHealthProbesAreAnonymous() throws Exception
    {
        assertEquals(200, mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                .get("/actuator/health/liveness")).andReturn().getResponse().getStatus());
        assertEquals(200, mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                .get("/actuator/health/readiness")).andReturn().getResponse().getStatus());
        assertEquals(401, mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                .post("/actuator/health/liveness")).andReturn().getResponse().getStatus());
        assertEquals(401, mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                .get("/actuator/env")).andReturn().getResponse().getStatus());
        assertEquals(401, mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                .get("/actuator/env").cookie(new Cookie("Admin-Token", "forged-cookie-token")))
                .andReturn().getResponse().getStatus());
        assertEquals(200, mvc.perform(org.springframework.test.web.servlet.request.MockMvcRequestBuilders
                .get("/actuator/health")).andReturn().getResponse().getStatus());
    }

    @Configuration
    @EnableWebMvc
    @org.springframework.context.annotation.Import(SecurityConfig.class)
    static class TestConfig
    {
        @Bean
        UserDetailsService userDetailsService()
        {
            return username -> User.withUsername(username).password("unused").roles("USER").build();
        }

        @Bean
        AuthenticationEntryPointImpl authenticationEntryPoint()
        {
            return new AuthenticationEntryPointImpl();
        }

        @Bean
        LogoutSuccessHandlerImpl logoutSuccessHandler()
        {
            return mock(LogoutSuccessHandlerImpl.class);
        }

        @Bean
        TokenService tokenService()
        {
            return mock(TokenService.class);
        }

        @Bean
        RedisCache redisCache()
        {
            return mock(RedisCache.class);
        }

        @Bean
        RedisTemplate<?, ?> redisTemplate()
        {
            return mock(RedisTemplate.class);
        }

        @Bean
        JwtAuthenticationTokenFilter authenticationTokenFilter(TokenService tokens,
                AuthenticationEntryPointImpl entryPoint)
        {
            JwtAuthenticationTokenFilter filter = new JwtAuthenticationTokenFilter();
            ReflectionTestUtils.setField(filter, "tokenService", tokens);
            ReflectionTestUtils.setField(filter, "unauthorizedHandler", entryPoint);
            return filter;
        }

        @Bean
        ProbeController probeController()
        {
            return new ProbeController();
        }
    }

    @RestController
    static class ProbeController
    {
        @GetMapping({"/actuator/health/liveness", "/actuator/health/readiness",
                "/actuator/health", "/actuator/env"})
        ResponseEntity<String> get()
        {
            return ResponseEntity.ok("ok");
        }

        @PostMapping("/actuator/health/liveness")
        ResponseEntity<String> post()
        {
            return ResponseEntity.ok("ok");
        }
    }
}
