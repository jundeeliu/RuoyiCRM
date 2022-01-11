package com.ruoyi.framework.datasource;

import com.alibaba.druid.pool.DruidDataSourceFactory;
import lombok.extern.slf4j.Slf4j;
import org.springframework.jdbc.datasource.lookup.AbstractRoutingDataSource;

import javax.sql.DataSource;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 动态数据源
 *
 * @author devjd
 */
@Slf4j
public class DynamicRoutingDataSource extends AbstractRoutingDataSource {

    private static Map<Object, Object> targetTargetDataSources = new ConcurrentHashMap<>();

    @Override
    protected Object determineCurrentLookupKey() {
        // 每次连接数据库，都会去设置数据源
        return DynamicDataSourceContextHolder.getDataSourceKey();
    }

    // 设置targetDataSources并记录数据源（这里可以记录每个数据源的最近使用时间，可以做删除不经常使用的数据源）
    @Override
    public void setTargetDataSources(Map<Object, Object> targetDataSources) {
        super.setTargetDataSources(targetDataSources);
        super.afterPropertiesSet();
        targetTargetDataSources = targetDataSources;
    }

    // 添加数据源
    public void addDataSource(String tenant, Map<String, Object> dataSourceProperties) {
        targetTargetDataSources.put(tenant, dataSource(dataSourceProperties));
        super.setTargetDataSources(targetTargetDataSources);
        afterPropertiesSet();
    }

    // 判断是否存在数据源，存在直接取
    public boolean existDataSource(String tenant) {
        return targetTargetDataSources.containsKey(tenant);
    }

    // 组装数据源
    public DataSource dataSource(Map<String, Object> dataSourceProperties) {
        DataSource dataSource;
        try {
            dataSource = DruidDataSourceFactory.createDataSource(dataSourceProperties);
        } catch (Exception e) {
            log.error("dataSource: {}", e);
            throw new RuntimeException();
        }
        return dataSource;
    }
}