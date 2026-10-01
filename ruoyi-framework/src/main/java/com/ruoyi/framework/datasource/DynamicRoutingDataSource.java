package com.ruoyi.framework.datasource;

import com.alibaba.druid.pool.DruidDataSourceFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.DisposableBean;
import org.springframework.jdbc.datasource.lookup.AbstractRoutingDataSource;

import javax.sql.DataSource;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.security.NoSuchAlgorithmException;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.TreeMap;
import java.util.concurrent.ConcurrentHashMap;
import java.util.concurrent.ConcurrentMap;

/** Request-scoped tenant routing. An absent or unknown key never opens master. */
@Slf4j
public class DynamicRoutingDataSource extends AbstractRoutingDataSource implements DisposableBean {

    public static final String MASTER_KEY = "MASTER";

    private final ConcurrentMap<String, DataSource> dataSources = new ConcurrentHashMap<>();
    private final ConcurrentMap<String, String> tenantConfigurationDigests = new ConcurrentHashMap<>();

    @Override
    protected Object determineCurrentLookupKey() {
        return DynamicDataSourceContextHolder.getDataSourceKey();
    }

    @Override
    protected DataSource determineTargetDataSource() {
        String key = DynamicDataSourceContextHolder.getDataSourceKey();
        if (key == null) {
            throw new IllegalStateException("No data source selected for the current thread");
        }
        DataSource selected = dataSources.get(key);
        if (selected == null) {
            throw new IllegalStateException("Unknown data source key: " + key);
        }
        return selected;
    }

    /** Configure the fixed master source once during bean creation. */
    @Override
    public synchronized void setTargetDataSources(Map<Object, Object> targets) {
        if (!dataSources.isEmpty()) {
            throw new IllegalStateException("Initial data sources are already configured");
        }
        if (targets == null || targets.size() != 1 || !(targets.get(MASTER_KEY) instanceof DataSource)) {
            throw new IllegalArgumentException("Exactly one explicit MASTER data source is required");
        }
        Map<Object, Object> snapshot = new HashMap<>(targets);
        super.setTargetDataSources(snapshot);
        dataSources.put(MASTER_KEY, (DataSource) snapshot.get(MASTER_KEY));
    }

    /** Concurrent first requests create one pool; changed credentials require controlled rotation. */
    public synchronized void addDataSource(String tenant, Map<String, Object> properties) {
        validateTenant(tenant);
        if (properties == null || properties.isEmpty()) {
            throw new IllegalArgumentException("Tenant data source properties are missing");
        }
        String digest = configurationDigest(properties);
        if (dataSources.containsKey(tenant)) {
            if (!digest.equals(tenantConfigurationDigests.get(tenant))) {
                throw new IllegalStateException("Tenant data source configuration changed; controlled rotation required");
            }
            return;
        }
        DataSource created = dataSource(properties);
        dataSources.put(tenant, created);
        tenantConfigurationDigests.put(tenant, digest);
    }

    public boolean existDataSource(String tenant) {
        return tenant != null && dataSources.containsKey(tenant);
    }

    public DataSource dataSource(Map<String, Object> properties) {
        try {
            return DruidDataSourceFactory.createDataSource(properties);
        } catch (Exception exception) {
            log.error("Unable to create data source");
            throw new IllegalStateException("Unable to create data source", exception);
        }
    }

    @Override
    public synchronized void destroy() throws Exception {
        Exception failure = null;
        for (DataSource source : new HashSet<>(dataSources.values())) {
            if (source instanceof AutoCloseable) {
                try {
                    ((AutoCloseable) source).close();
                } catch (Exception exception) {
                    if (failure == null) {
                        failure = exception;
                    } else {
                        failure.addSuppressed(exception);
                    }
                }
            }
        }
        dataSources.clear();
        tenantConfigurationDigests.clear();
        if (failure != null) {
            throw failure;
        }
    }

    private static void validateTenant(String tenant) {
        if (tenant == null || tenant.trim().isEmpty() || MASTER_KEY.equalsIgnoreCase(tenant)) {
            throw new IllegalArgumentException("Invalid tenant data source key");
        }
    }

    private static String configurationDigest(Map<String, Object> properties) {
        try {
            MessageDigest digest = MessageDigest.getInstance("SHA-256");
            for (Map.Entry<String, Object> entry : new TreeMap<>(properties).entrySet()) {
                updateField(digest, entry.getKey());
                updateField(digest, String.valueOf(entry.getValue()));
            }
            byte[] bytes = digest.digest();
            StringBuilder hex = new StringBuilder(bytes.length * 2);
            for (byte value : bytes) {
                hex.append(Character.forDigit((value >>> 4) & 0xF, 16));
                hex.append(Character.forDigit(value & 0xF, 16));
            }
            return hex.toString();
        } catch (NoSuchAlgorithmException exception) {
            throw new IllegalStateException("SHA-256 is unavailable", exception);
        }
    }

    private static void updateField(MessageDigest digest, String value) {
        byte[] bytes = value.getBytes(StandardCharsets.UTF_8);
        digest.update((byte) (bytes.length >>> 24));
        digest.update((byte) (bytes.length >>> 16));
        digest.update((byte) (bytes.length >>> 8));
        digest.update((byte) bytes.length);
        digest.update(bytes);
    }
}
