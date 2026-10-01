package com.ruoyi.framework.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertThrows;

import com.ruoyi.framework.config.ResourcesConfig;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.test.util.ReflectionTestUtils;
import org.springframework.web.cors.CorsConfiguration;

class CorsConfigurationTest
{
    @Test
    void onlyConfiguredOriginCanUseCrossOriginApi()
    {
        ResourcesConfig resources = new ResourcesConfig();
        ReflectionTestUtils.setField(resources, "allowedOrigins", "https://console.example.com");
        MockHttpServletRequest request = new MockHttpServletRequest("OPTIONS", "/system/user/list");
        CorsConfiguration cors = resources.corsConfigurationSource().getCorsConfiguration(request);

        assertEquals("https://console.example.com", cors.checkOrigin("https://console.example.com"));
        assertEquals(null, cors.checkOrigin("https://attacker.example.com"));
        assertFalse(cors.getAllowCredentials());
    }

    @Test
    void rejectsWildcardOrigin()
    {
        ResourcesConfig resources = new ResourcesConfig();
        ReflectionTestUtils.setField(resources, "allowedOrigins", "https://*.example.com");
        assertThrows(IllegalArgumentException.class, resources::corsConfigurationSource);
    }
}
