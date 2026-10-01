package com.ruoyi.framework.datasource;

import org.springframework.transaction.support.TransactionSynchronizationManager;

/**
 * 数据源切换处理
 *
 * @author devjd
 */

public final class DynamicDataSourceContextHolder {

    private static final ThreadLocal<String> db = new ThreadLocal<>();

    private DynamicDataSourceContextHolder() {
    }

    public static void setDataSourceKey(String key) {
        if (key == null || key.trim().isEmpty()) {
            throw new IllegalArgumentException("Data source key must not be blank");
        }
        String previous = db.get();
        if (!key.equals(previous) && (TransactionSynchronizationManager.isActualTransactionActive()
                || TransactionSynchronizationManager.isSynchronizationActive())) {
            throw new IllegalStateException("Cannot switch data source while a transaction is bound");
        }
        db.set(key);
    }

    public static String getDataSourceKey() {
        return db.get();
    }

    public static void clearDataSourceKey() {
        db.remove();
    }
}
