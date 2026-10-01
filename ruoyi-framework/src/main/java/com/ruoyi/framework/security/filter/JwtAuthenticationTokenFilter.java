package com.ruoyi.framework.security.filter;

import java.io.IOException;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.BadCredentialsException;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.framework.security.handle.AuthenticationEntryPointImpl;
import com.ruoyi.framework.web.service.TokenService;

/**
 * token过滤器 验证token有效性
 * 
 * @author ruoyi
 */
@Component
public class JwtAuthenticationTokenFilter extends OncePerRequestFilter
{
    @Autowired
    private TokenService tokenService;

    @Autowired
    private AuthenticationEntryPointImpl unauthorizedHandler;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain chain)
            throws ServletException, IOException
    {
        LoginUser loginUser = tokenService.getLoginUser(request);
        if (loginUser == null && tokenService.hasToken(request))
        {
            SecurityContextHolder.clearContext();
            unauthorizedHandler.commence(request, response, new BadCredentialsException("令牌无效"));
            return;
        }
        if (loginUser != null)
        {
            String tenant = request.getHeader("tenant");
            // Tenant IDs select a physical data source. Require exact equality
            // even if an Authentication was already present in this context.
            if (tenant == null || tenant.isBlank() || loginUser.getTenant() == null
                    || !loginUser.getTenant().equals(tenant))
            {
                SecurityContextHolder.clearContext();
                unauthorizedHandler.commence(request, response, new BadCredentialsException("令牌租户不匹配"));
                return;
            }
            tokenService.verifyToken(loginUser);
            if (SecurityContextHolder.getContext().getAuthentication() == null)
            {
                UsernamePasswordAuthenticationToken authenticationToken =
                        new UsernamePasswordAuthenticationToken(loginUser, null, loginUser.getAuthorities());
                authenticationToken.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                SecurityContextHolder.getContext().setAuthentication(authenticationToken);
            }
        }
        chain.doFilter(request, response);
    }
}
