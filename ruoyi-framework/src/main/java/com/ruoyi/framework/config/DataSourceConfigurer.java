package com.ruoyi.framework.config;

import com.ruoyi.framework.datasource.DynamicRoutingDataSource;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;
import javax.sql.DataSource;

@Configuration
public class DataSourceConfigurer {

    @Value("${spring.datasource.druid.master.url}")
    private String url;

    @Value("${spring.datasource.druid.master.username}")
    private String username;

    @Value("${spring.datasource.druid.master.password}")
    private String password;

    @Value("${spring.datasource.driverClassName}")
    private String driverClassName;

    private Map<String, Object> getProperties() {
        Map<String, Object> map = new HashMap<>();
        map.put("driverClassName", driverClassName);
        map.put("url", url);
        map.put("username", username);
        map.put("password", password);
        return map;
    }

    @Bean("dynamicDataSource")
    public DynamicRoutingDataSource dynamicDataSource() {
        DynamicRoutingDataSource dynamicRoutingDataSource = new DynamicRoutingDataSource();
        Map<Object, Object> dataSourceMap = new HashMap<>(1);
        DataSource master = dynamicRoutingDataSource.dataSource(getProperties());
        dataSourceMap.put(DynamicRoutingDataSource.MASTER_KEY, master);
        dynamicRoutingDataSource.setTargetDataSources(dataSourceMap);
        dynamicRoutingDataSource.setLenientFallback(false);
        return dynamicRoutingDataSource;
    }
}
