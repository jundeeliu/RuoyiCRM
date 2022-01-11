package com.ruoyi.framework.config;

import com.ruoyi.framework.datasource.DynamicRoutingDataSource;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.HashMap;
import java.util.Map;

@Configuration
@Slf4j
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
        dataSourceMap.put("default_db", dynamicRoutingDataSource.dataSource(getProperties()));
        dynamicRoutingDataSource.setTargetDataSources(dataSourceMap);
        dynamicRoutingDataSource.setDefaultTargetDataSource(dynamicRoutingDataSource.dataSource(getProperties()));
        return dynamicRoutingDataSource;
    }
}