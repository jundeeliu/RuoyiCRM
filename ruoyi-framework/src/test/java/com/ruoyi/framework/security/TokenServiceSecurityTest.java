package com.ruoyi.framework.security;

import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertSame;
import static org.junit.jupiter.api.Assertions.assertThrows;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import java.util.Base64;
import javax.crypto.SecretKey;
import com.ruoyi.common.constant.Constants;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.core.redis.RedisCache;
import com.ruoyi.framework.web.service.TokenService;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.test.util.ReflectionTestUtils;

class TokenServiceSecurityTest
{
    private final TokenService service = new TokenService();
    private final RedisCache cache = mock(RedisCache.class);
    private final byte[] keyBytes = new byte[64];

    @BeforeEach
    void setUp()
    {
        for (int i = 0; i < keyBytes.length; i++)
        {
            keyBytes[i] = (byte) (i + 1);
        }
        ReflectionTestUtils.setField(service, "header", "Authorization");
        ReflectionTestUtils.setField(service, "redisCache", cache);
    }

    @Test
    void rejectsWeakSigningKeyAtStartup()
    {
        ReflectionTestUtils.setField(service, "secret", Base64.getEncoder().encodeToString(new byte[26]));
        assertThrows(IllegalStateException.class, service::initializeSigningKey);
    }

    @Test
    void rejectsTokenWhoseSignedTenantDiffersFromCachedUser()
    {
        ReflectionTestUtils.setField(service, "secret", Base64.getEncoder().encodeToString(keyBytes));
        service.initializeSigningKey();
        SecretKey key = Keys.hmacShaKeyFor(keyBytes);
        String token = Jwts.builder()
                .claim(Constants.LOGIN_USER_KEY, "session-1")
                .claim(Constants.LOGIN_TENANT_KEY, "tenant-a")
                .signWith(key, Jwts.SIG.HS512).compact();
        LoginUser user = new LoginUser();
        user.setTenant("tenant-b");
        when(cache.getCacheObject(Constants.LOGIN_TOKEN_KEY + "session-1")).thenReturn(user);
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", Constants.TOKEN_PREFIX + token);

        assertNull(service.getLoginUser(request));

        user.setTenant("tenant-a");
        assertSame(user, service.getLoginUser(request));
    }

    @Test
    void rejectsUnsignedOrMalformedToken()
    {
        ReflectionTestUtils.setField(service, "secret", Base64.getEncoder().encodeToString(keyBytes));
        service.initializeSigningKey();
        MockHttpServletRequest request = new MockHttpServletRequest();
        request.addHeader("Authorization", "Bearer invalid.token.payload");
        assertNull(service.getLoginUser(request));
    }
}
