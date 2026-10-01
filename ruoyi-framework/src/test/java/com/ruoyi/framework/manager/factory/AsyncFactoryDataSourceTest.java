package com.ruoyi.framework.manager.factory;

import com.ruoyi.framework.datasource.DynamicDataSourceContextHolder;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;

import static org.junit.jupiter.api.Assertions.*;

class AsyncFactoryDataSourceTest {

    @AfterEach
    void clear() {
        DynamicDataSourceContextHolder.clearDataSourceKey();
    }

    @Test
    void workerCannotInheritPreviousTenantAndAlwaysClearsOnFailure() {
        DynamicDataSourceContextHolder.setDataSourceKey("old-tenant");
        assertThrows(IllegalStateException.class,
                () -> AsyncFactory.runInDataSource("new-tenant", () -> {
                    assertEquals("new-tenant", DynamicDataSourceContextHolder.getDataSourceKey());
                    throw new IllegalStateException("write failed");
                }));
        assertNull(DynamicDataSourceContextHolder.getDataSourceKey());
    }

    @Test
    void systemAuditUsesExplicitMasterRatherThanImplicitFallback() {
        AsyncFactory.runInDataSource(null,
                () -> assertEquals("MASTER", DynamicDataSourceContextHolder.getDataSourceKey()));
        assertNull(DynamicDataSourceContextHolder.getDataSourceKey());
    }
}
