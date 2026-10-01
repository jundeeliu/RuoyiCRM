package com.ruoyi.framework.datasource;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Assumptions;
import org.junit.jupiter.api.Test;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.CannotGetJdbcConnectionException;
import org.springframework.jdbc.datasource.DataSourceTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;

import javax.sql.DataSource;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;
import java.util.Properties;
import java.util.UUID;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.*;

/** Runs only when pointed at the disposable, loopback CRIT-10 Compose stack. */
class DisposableMySqlTenantRoutingTest {

    @AfterEach
    void clearContext() {
        DynamicDataSourceContextHolder.clearDataSourceKey();
    }

    @Test
    void realConnectionsRemainInTheirTenantAndRollbackDoesNotPolluteEitherDatabase() throws Exception {
        Stack stack = Stack.fromEnvironment();
        DynamicRoutingDataSource router = new DynamicRoutingDataSource();
        DataSource master = router.dataSource(stack.properties("rycrm-master"));
        router.setTargetDataSources(Map.of(DynamicRoutingDataSource.MASTER_KEY, master));
        router.afterPropertiesSet();
        router.addDataSource("tenant1", stack.properties("rycrm-tenant-1"));
        router.addDataSource("tenant2", stack.properties("rycrm-tenant-2"));

        ExecutorService observer = Executors.newSingleThreadExecutor();
        try {
            JdbcTemplate jdbc = new JdbcTemplate(router);
            DynamicDataSourceContextHolder.setDataSourceKey(DynamicRoutingDataSource.MASTER_KEY);
            assertEquals("rycrm-master", jdbc.queryForObject("SELECT DATABASE()", String.class));
            DynamicDataSourceContextHolder.setDataSourceKey("tenant1");
            assertEquals("rycrm-tenant-1", jdbc.queryForObject("SELECT DATABASE()", String.class));

            String marker = "crit06_" + UUID.randomUUID().toString().replace("-", "");
            TransactionTemplate transaction = new TransactionTemplate(new DataSourceTransactionManager(router));
            transaction.execute(status -> {
                assertEquals("rycrm-tenant-1", jdbc.queryForObject("SELECT DATABASE()", String.class));
                jdbc.update("INSERT INTO sys_config (config_name, config_key, config_value) VALUES (?, ?, ?)",
                        "disposable route test", marker, "tenant-one-only");
                assertEquals(1, countMarker(jdbc, marker));
                assertThrows(IllegalStateException.class,
                        () -> DynamicDataSourceContextHolder.setDataSourceKey("tenant2"));
                assertEquals("tenant1", DynamicDataSourceContextHolder.getDataSourceKey());

                Future<Integer> otherTenant = observer.submit(() -> {
                    DynamicDataSourceContextHolder.setDataSourceKey("tenant2");
                    try {
                        assertEquals("rycrm-tenant-2", jdbc.queryForObject("SELECT DATABASE()", String.class));
                        return countMarker(jdbc, marker);
                    } finally {
                        DynamicDataSourceContextHolder.clearDataSourceKey();
                    }
                });
                try {
                    assertEquals(0, otherTenant.get(15, TimeUnit.SECONDS));
                } catch (Exception exception) {
                    throw new IllegalStateException("Tenant observer failed", exception);
                }
                status.setRollbackOnly();
                return null;
            });

            assertEquals(0, countMarker(jdbc, marker));
            DynamicDataSourceContextHolder.setDataSourceKey("tenant2");
            assertEquals(0, countMarker(jdbc, marker));
            DynamicDataSourceContextHolder.setDataSourceKey("missing");
            CannotGetJdbcConnectionException unknown = assertThrows(CannotGetJdbcConnectionException.class,
                    () -> jdbc.queryForObject("SELECT DATABASE()", String.class));
            assertInstanceOf(IllegalStateException.class, unknown.getCause());
            DynamicDataSourceContextHolder.clearDataSourceKey();
            CannotGetJdbcConnectionException absent = assertThrows(CannotGetJdbcConnectionException.class,
                    () -> jdbc.queryForObject("SELECT DATABASE()", String.class));
            assertInstanceOf(IllegalStateException.class, absent.getCause());
        } finally {
            observer.shutdownNow();
            DynamicDataSourceContextHolder.clearDataSourceKey();
            router.destroy();
        }
    }

    private static int countMarker(JdbcTemplate jdbc, String marker) {
        Integer count = jdbc.queryForObject("SELECT COUNT(*) FROM sys_config WHERE config_key = ?", Integer.class,
                marker);
        return count == null ? -1 : count;
    }

    private static final class Stack {
        private final int port;
        private final String user;
        private final String password;

        private Stack(int port, String user, String password) {
            this.port = port;
            this.user = user;
            this.password = password;
        }

        static Stack fromEnvironment() throws IOException {
            String location = System.getenv("RUOYICRM_CRIT10_STATE");
            Assumptions.assumeTrue(location != null && !location.isBlank(),
                    "Set RUOYICRM_CRIT10_STATE to a disposable stack state.json");
            Path stateFile = Path.of(location).toRealPath();
            Path runtime = stateFile.getParent();
            if (!"state.json".equals(stateFile.getFileName().toString())
                    || !runtime.getFileName().toString().startsWith("ruoyicrm-crit10-")) {
                throw new IllegalStateException("Refusing a non-disposable database state path");
            }
            ObjectMapper mapper = new ObjectMapper();
            JsonNode state = mapper.readTree(stateFile.toFile());
            JsonNode receipt = mapper.readTree(runtime.resolve("probe-receipt.json").toFile());
            String project = state.path("project").asText();
            int port = state.path("mysql_port").asInt();
            if (!"ruoyicrm.crit10.local-stack.v1".equals(state.path("schema").asText())
                    || !project.startsWith("ruoyicrm-crit10-")
                    || !project.equals(receipt.path("project").asText())
                    || !"LOCAL_PHYSICAL_STACK_READY".equals(receipt.path("status").asText())
                    || !"127.0.0.1".equals(receipt.path("bindings").path("mysql").path("host").asText())
                    || port != receipt.path("bindings").path("mysql").path("port").asInt()
                    || port < 1024 || port > 65535) {
                throw new IllegalStateException("Disposable stack identity or probe is invalid");
            }
            Properties credentials = new Properties();
            try (var reader = Files.newBufferedReader(runtime.resolve("mysql-app.cnf"))) {
                credentials.load(reader);
            }
            String user = credentials.getProperty("user");
            String password = credentials.getProperty("password");
            if (!"crit10_app".equals(user) || password == null || password.isBlank()) {
                throw new IllegalStateException("Disposable app credentials are unavailable");
            }
            return new Stack(port, user, password);
        }

        Map<String, Object> properties(String database) {
            if (!database.equals("rycrm-master") && !database.equals("rycrm-tenant-1")
                    && !database.equals("rycrm-tenant-2")) {
                throw new IllegalArgumentException("Database is outside the disposable allowlist");
            }
            Map<String, Object> properties = new HashMap<>();
            properties.put("driverClassName", "com.mysql.cj.jdbc.Driver");
            properties.put("url", "jdbc:mysql://127.0.0.1:" + port + "/" + database
                    + "?sslMode=DISABLED&allowPublicKeyRetrieval=true");
            properties.put("username", user);
            properties.put("password", password);
            return properties;
        }
    }
}
