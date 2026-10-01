package com.ruoyi.framework.datasource;

import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.datasource.AbstractDataSource;

import javax.sql.DataSource;
import java.sql.Connection;
import java.sql.SQLException;
import java.util.HashMap;
import java.util.Map;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.jupiter.api.Assertions.*;

class DynamicRoutingDataSourceTest {

    private static final DataSource STUB = new AbstractDataSource() {
        @Override public Connection getConnection() throws SQLException { return null; }
        @Override public Connection getConnection(String username, String password) throws SQLException { return null; }
    };

    @AfterEach
    void clearContext() {
        DynamicDataSourceContextHolder.clearDataSourceKey();
    }

    @Test
    void absentAndUnknownTenantNeverFallBackToMaster() throws Exception {
        DynamicRoutingDataSource router = router();
        assertThrows(IllegalStateException.class, router::getConnection);
        DynamicDataSourceContextHolder.setDataSourceKey("missing");
        assertThrows(IllegalStateException.class, router::getConnection);
        DynamicDataSourceContextHolder.setDataSourceKey(DynamicRoutingDataSource.MASTER_KEY);
        assertNull(router.getConnection());
    }

    @Test
    void registriesAreInstanceScopedAndCredentialDriftFailsClosed() {
        CountingRouter one = new CountingRouter();
        one.setTargetDataSources(Map.of(DynamicRoutingDataSource.MASTER_KEY, STUB));
        DynamicRoutingDataSource two = router();
        Map<String, Object> props = new HashMap<>();
        props.put("url", "jdbc:synthetic:tenant-one");
        props.put("password", "first");
        one.addDataSource("tenant-one", props);
        assertTrue(one.existDataSource("tenant-one"));
        assertFalse(two.existDataSource("tenant-one"));
        props.put("password", "changed");
        assertThrows(IllegalStateException.class, () -> one.addDataSource("tenant-one", props));
        assertEquals(1, one.creations.get());
        assertThrows(IllegalArgumentException.class,
                () -> one.addDataSource(DynamicRoutingDataSource.MASTER_KEY, props));
    }

    @Test
    void concurrentFirstRequestsCreateOnePool() throws Exception {
        CountingRouter router = new CountingRouter();
        router.setTargetDataSources(Map.of(DynamicRoutingDataSource.MASTER_KEY, STUB));
        Map<String, Object> props = Map.of("url", "jdbc:synthetic:tenant-one", "password", "secret");
        ExecutorService workers = Executors.newFixedThreadPool(8);
        CountDownLatch start = new CountDownLatch(1);
        try {
            Future<?>[] futures = new Future<?>[8];
            for (int index = 0; index < futures.length; index++) {
                futures[index] = workers.submit(() -> {
                    start.await();
                    router.addDataSource("tenant-one", props);
                    return null;
                });
            }
            start.countDown();
            for (Future<?> future : futures) {
                future.get();
            }
            assertEquals(1, router.creations.get());
        } finally {
            workers.shutdownNow();
        }
    }

    private static DynamicRoutingDataSource router() {
        DynamicRoutingDataSource router = new DynamicRoutingDataSource();
        router.setTargetDataSources(Map.of(DynamicRoutingDataSource.MASTER_KEY, STUB));
        return router;
    }

    private static final class CountingRouter extends DynamicRoutingDataSource {
        private final AtomicInteger creations = new AtomicInteger();

        @Override
        public DataSource dataSource(Map<String, Object> properties) {
            creations.incrementAndGet();
            return STUB;
        }
    }
}
