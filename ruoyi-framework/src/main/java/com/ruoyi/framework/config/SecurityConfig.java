package com.ruoyi.framework.config;

import com.ruoyi.framework.security.filter.JwtAuthenticationTokenFilter;
import com.ruoyi.framework.security.handle.AuthenticationEntryPointImpl;
import com.ruoyi.framework.security.handle.LogoutSuccessHandlerImpl;
import org.springframework.boot.web.servlet.FilterRegistrationBean;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.http.HttpMethod;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.ProviderManager;
import org.springframework.security.authentication.dao.DaoAuthenticationProvider;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.security.web.util.matcher.RegexRequestMatcher;

/** Stateless bearer-token security configuration for the API. */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true, securedEnabled = true)
public class SecurityConfig
{
    @Bean
    public BCryptPasswordEncoder bCryptPasswordEncoder()
    {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public FilterRegistrationBean<JwtAuthenticationTokenFilter> jwtFilterRegistration(
            JwtAuthenticationTokenFilter authenticationTokenFilter)
    {
        FilterRegistrationBean<JwtAuthenticationTokenFilter> registration =
                new FilterRegistrationBean<>(authenticationTokenFilter);
        registration.setEnabled(false);
        return registration;
    }

    @Bean
    public AuthenticationManager authenticationManager(UserDetailsService userDetailsService,
            BCryptPasswordEncoder passwordEncoder)
    {
        DaoAuthenticationProvider provider = new DaoAuthenticationProvider(userDetailsService);
        provider.setPasswordEncoder(passwordEncoder);
        return new ProviderManager(provider);
    }

    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http,
            AuthenticationEntryPointImpl unauthorizedHandler,
            LogoutSuccessHandlerImpl logoutSuccessHandler,
            JwtAuthenticationTokenFilter authenticationTokenFilter) throws Exception
    {
        http
            // Authentication is sent in an Authorization header, not a browser cookie.
            .csrf(AbstractHttpConfigurer::disable)
            .cors(cors -> { })
            .exceptionHandling(exceptions -> exceptions.authenticationEntryPoint(unauthorizedHandler))
            .sessionManagement(session -> session.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
            .authorizeHttpRequests(authorize -> authorize
                .requestMatchers("/login", "/register", "/captchaImage").anonymous()
                .requestMatchers(HttpMethod.GET, "/", "/profile/**").permitAll()
                // Spring Security 7 PathPattern matchers reject the old '/**/*.js'
                // pattern. This regex retains GET-only access to static assets.
                .requestMatchers(new RegexRequestMatcher("^/.*\\.(?:html|css|js)(?:\\?.*)?$", "GET")).permitAll()
                .requestMatchers("/swagger-ui.html", "/swagger-ui/**", "/swagger-resources/**",
                        "/webjars/**", "/{segment}/api-docs", "/v3/api-docs/**").anonymous()
                .requestMatchers(HttpMethod.GET, "/actuator/health", "/actuator/health/liveness",
                        "/actuator/health/readiness").permitAll()
                .anyRequest().authenticated())
            .headers(headers -> headers.frameOptions(frame -> frame.sameOrigin()))
            .logout(logout -> logout.logoutUrl("/logout").logoutSuccessHandler(logoutSuccessHandler))
            .addFilterBefore(authenticationTokenFilter, UsernamePasswordAuthenticationFilter.class);
        return http.build();
    }
}
