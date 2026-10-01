package com.ruoyi.framework.config;

import com.ruoyi.framework.interceptor.TenantInterceptor;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.servlet.config.annotation.InterceptorRegistry;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;
import com.ruoyi.common.config.RuoYiConfig;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.framework.interceptor.RepeatSubmitInterceptor;

/**
 * 通用配置
 * 
 * @author ruoyi
 */
@Configuration
public class ResourcesConfig implements WebMvcConfigurer
{
    @Value("${security.cors.allowed-origins:}")
    private String allowedOrigins;
    @Autowired
    private RepeatSubmitInterceptor repeatSubmitInterceptor;

    @Autowired
    private TenantInterceptor tenantInterceptor;

    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry)
    {
        /** 本地文件上传路径 */
        registry.addResourceHandler(Constants.RESOURCE_PREFIX + "/**")
                .addResourceLocations("file:" + RuoYiConfig.getProfile() + "/");

    }

    /**
     * 自定义拦截规则
     */
    @Override
    public void addInterceptors(InterceptorRegistry registry)
    {
        registry.addInterceptor(repeatSubmitInterceptor).addPathPatterns("/**");
        registry.addInterceptor(tenantInterceptor).addPathPatterns("/**").excludePathPatterns("/captchaImage").excludePathPatterns("/register");
    }

    /**
     * 跨域配置
     */
    @Bean
    public CorsConfigurationSource corsConfigurationSource()
    {
        CorsConfiguration config = new CorsConfiguration();
        // The UI normally uses a same-origin proxy. Cross-origin deployment
        // must list trusted origins explicitly; credentials and wildcard
        // origins cannot be safely combined.
        if (allowedOrigins != null)
        {
            for (String value : allowedOrigins.split(","))
            {
                String origin = value.trim();
                if (!origin.isEmpty())
                {
                    if (origin.contains("*"))
                    {
                        throw new IllegalArgumentException("security.cors.allowed-origins must contain exact origins");
                    }
                    config.addAllowedOrigin(origin);
                }
            }
        }
        config.setAllowCredentials(false);
        config.setAllowedHeaders(java.util.List.of("Authorization", "Content-Type", "tenant", "X-Requested-With"));
        config.setAllowedMethods(java.util.List.of("GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"));
        config.setMaxAge(1800L);
        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        return source;
    }
}
