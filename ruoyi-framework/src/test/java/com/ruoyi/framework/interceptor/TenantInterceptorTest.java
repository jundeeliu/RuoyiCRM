package com.ruoyi.framework.interceptor;

import com.ruoyi.framework.datasource.DynamicDataSourceContextHolder;
import com.ruoyi.framework.datasource.DynamicRoutingDataSource;
import com.ruoyi.tenant.domain.MasterTenant;
import com.ruoyi.tenant.domain.enums.TenantStatus;
import com.ruoyi.tenant.service.IMasterTenantService;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.mock.web.MockHttpServletRequest;
import org.springframework.mock.web.MockHttpServletResponse;
import org.springframework.test.util.ReflectionTestUtils;

import java.util.Date;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class TenantInterceptorTest {

    private final IMasterTenantService tenants = mock(IMasterTenantService.class);
    private final DynamicRoutingDataSource router = mock(DynamicRoutingDataSource.class);
    private final TenantInterceptor interceptor = new TenantInterceptor();

    TenantInterceptorTest() {
        ReflectionTestUtils.setField(interceptor, "masterTenantService", tenants);
        ReflectionTestUtils.setField(interceptor, "dynamicRoutingDataSource", router);
        ReflectionTestUtils.setField(interceptor, "driverClassName", "org.example.Driver");
    }

    @AfterEach
    void clearContext() {
        DynamicDataSourceContextHolder.clearDataSourceKey();
    }

    @Test
    void missingTenantClearsLeakedPreviousRequestKey() {
        DynamicDataSourceContextHolder.setDataSourceKey("previous-tenant");
        assertThrows(IllegalArgumentException.class,
                () -> interceptor.preHandle(request(null), new MockHttpServletResponse(), new Object()));
        assertNull(DynamicDataSourceContextHolder.getDataSourceKey());
        verifyNoInteractions(tenants, router);
    }

    @Test
    void cachedTenantIsRevalidatedAndDisabledTenantDoesNotBind() {
        MasterTenant record = activeTenant();
        when(tenants.selectMasterTenant("tenant-a")).thenReturn(record);
        MockHttpServletRequest request = request("tenant-a");
        MockHttpServletResponse response = new MockHttpServletResponse();
        assertTrue(interceptor.preHandle(request, response, new Object()));
        assertEquals("tenant-a", DynamicDataSourceContextHolder.getDataSourceKey());
        interceptor.afterCompletion(request, response, new Object(), null);
        assertNull(DynamicDataSourceContextHolder.getDataSourceKey());

        record.setStatus(TenantStatus.DISABLE.getCode());
        assertThrows(IllegalStateException.class,
                () -> interceptor.preHandle(request, response, new Object()));
        assertNull(DynamicDataSourceContextHolder.getDataSourceKey());
        verify(tenants, times(2)).selectMasterTenant("tenant-a");
        verify(router, times(1)).addDataSource(eq("tenant-a"), anyMap());
    }

    @Test
    void failedRegistrationAndAsyncHandoffClearThreadKey() {
        when(tenants.selectMasterTenant("tenant-a")).thenReturn(activeTenant());
        doThrow(new IllegalStateException("pool failed")).when(router).addDataSource(eq("tenant-a"), anyMap());
        MockHttpServletRequest request = request("tenant-a");
        MockHttpServletResponse response = new MockHttpServletResponse();
        assertThrows(IllegalStateException.class,
                () -> interceptor.preHandle(request, response, new Object()));
        assertNull(DynamicDataSourceContextHolder.getDataSourceKey());

        reset(router);
        assertTrue(interceptor.preHandle(request, response, new Object()));
        interceptor.afterConcurrentHandlingStarted(request, response, new Object());
        assertNull(DynamicDataSourceContextHolder.getDataSourceKey());
    }

    private static MockHttpServletRequest request(String tenant) {
        MockHttpServletRequest request = new MockHttpServletRequest();
        if (tenant != null) {
            request.addHeader("tenant", tenant);
        }
        return request;
    }

    private static MasterTenant activeTenant() {
        MasterTenant tenant = new MasterTenant();
        tenant.setTenant("tenant-a");
        tenant.setStatus(TenantStatus.NORMAL.getCode());
        tenant.setUrl("jdbc:synthetic:tenant-a");
        tenant.setUsername("app");
        tenant.setPassword("secret");
        tenant.setExpirationDate(new Date(System.currentTimeMillis() + 60_000));
        return tenant;
    }
}
