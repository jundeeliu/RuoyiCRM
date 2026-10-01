package com.ruoyi.framework.security;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.never;
import static org.mockito.Mockito.verify;
import static org.mockito.Mockito.when;

import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.framework.security.filter.JwtAuthenticationTokenFilter;
import com.ruoyi.framework.security.handle.AuthenticationEntryPointImpl;
import com.ruoyi.framework.web.service.TokenService;
import jakarta.servlet.FilterChain;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.test.util.ReflectionTestUtils;

class JwtAuthenticationTokenFilterTest
{
    private final TokenService tokens = mock(TokenService.class);
    private final JwtAuthenticationTokenFilter filter = new JwtAuthenticationTokenFilter();

    JwtAuthenticationTokenFilterTest()
    {
        ReflectionTestUtils.setField(filter, "tokenService", tokens);
        ReflectionTestUtils.setField(filter, "unauthorizedHandler", new AuthenticationEntryPointImpl());
    }

    @AfterEach
    void clearContext()
    {
        SecurityContextHolder.clearContext();
    }

    @Test
    void rejectsMissingOrDifferentTenantBeforeDatabaseRouting() throws Exception
    {
        LoginUser user = new LoginUser();
        user.setTenant("tenant-a");
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/system/user/list");
        MockHttpServletResponse response = new MockHttpServletResponse();
        FilterChain chain = mock(FilterChain.class);
        when(tokens.getLoginUser(request)).thenReturn(user);

        filter.doFilter(request, response, chain);

        assertEquals(401, response.getStatus());
        assertNull(SecurityContextHolder.getContext().getAuthentication());
        verify(tokens, never()).verifyToken(user);
        verify(chain, never()).doFilter(request, response);

        request.addHeader("tenant", "TENANT-A");
        response = new MockHttpServletResponse();
        filter.doFilter(request, response, chain);
        assertEquals(401, response.getStatus());
    }

    @Test
    void rejectsInvalidPresentedToken() throws Exception
    {
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/system/user/list");
        MockHttpServletResponse response = new MockHttpServletResponse();
        FilterChain chain = mock(FilterChain.class);
        when(tokens.hasToken(request)).thenReturn(true);

        filter.doFilter(request, response, chain);

        assertEquals(401, response.getStatus());
        verify(chain, never()).doFilter(request, response);
    }

    @Test
    void matchingTenantAuthenticatesAndContinues() throws Exception
    {
        LoginUser user = new LoginUser();
        user.setTenant("tenant-a");
        MockHttpServletRequest request = new MockHttpServletRequest("GET", "/system/user/list");
        request.addHeader("tenant", "tenant-a");
        MockHttpServletResponse response = new MockHttpServletResponse();
        FilterChain chain = mock(FilterChain.class);
        when(tokens.getLoginUser(request)).thenReturn(user);

        filter.doFilter(request, response, chain);

        assertSame(user, SecurityContextHolder.getContext().getAuthentication().getPrincipal());
        verify(tokens).verifyToken(user);
        verify(chain).doFilter(request, response);
    }
}
