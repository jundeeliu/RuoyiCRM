package com.ruoyi.framework.interceptor;

import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.framework.datasource.DynamicDataSourceContextHolder;
import com.ruoyi.framework.datasource.DynamicRoutingDataSource;
import com.ruoyi.tenant.domain.MasterTenant;
import com.ruoyi.tenant.domain.enums.TenantStatus;
import com.ruoyi.tenant.service.IMasterTenantService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.AsyncHandlerInterceptor;

import java.util.HashMap;
import java.util.Map;

/** Binds only a currently valid tenant to the request thread. */
@Component
public class TenantInterceptor implements AsyncHandlerInterceptor {

    @Autowired
    private IMasterTenantService masterTenantService;

    @Autowired
    private DynamicRoutingDataSource dynamicRoutingDataSource;

    @Value("${spring.datasource.driverClassName}")
    private String driverClassName;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) {
        // Servlet threads are reused. A leaked key from an earlier request must never
        // influence the master lookup or the current request.
        DynamicDataSourceContextHolder.clearDataSourceKey();
        boolean bound = false;
        try {
            String tenant = request.getHeader("tenant");
            if (tenant == null || tenant.trim().isEmpty() || !tenant.equals(tenant.trim())
                    || DynamicRoutingDataSource.MASTER_KEY.equalsIgnoreCase(tenant)) {
                throw new IllegalArgumentException("Missing or invalid tenant header");
            }

            // Always re-check status and expiry, including a tenant with a cached pool.
            MasterTenant record = masterTenantService.selectMasterTenant(tenant);
            if (record == null || !tenant.equals(record.getTenant())) {
                throw new IllegalArgumentException("Unknown tenant");
            }
            if (!TenantStatus.NORMAL.getCode().equals(record.getStatus())) {
                throw new IllegalStateException("Tenant is not active");
            }
            if (record.getExpirationDate() != null && !record.getExpirationDate().after(DateUtils.getNowDate())) {
                throw new IllegalStateException("Tenant has expired");
            }

            Map<String, Object> properties = new HashMap<>();
            properties.put("driverClassName", driverClassName);
            properties.put("url", record.getUrl());
            properties.put("username", record.getUsername());
            properties.put("password", record.getPassword());
            dynamicRoutingDataSource.addDataSource(tenant, properties);
            DynamicDataSourceContextHolder.setDataSourceKey(tenant);
            bound = true;
            return true;
        } finally {
            // Spring does not call afterCompletion when preHandle fails.
            if (!bound) {
                DynamicDataSourceContextHolder.clearDataSourceKey();
            }
        }
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler,
                                Exception exception) {
        DynamicDataSourceContextHolder.clearDataSourceKey();
    }

    @Override
    public void afterConcurrentHandlingStarted(HttpServletRequest request, HttpServletResponse response,
                                               Object handler) {
        DynamicDataSourceContextHolder.clearDataSourceKey();
    }
}
