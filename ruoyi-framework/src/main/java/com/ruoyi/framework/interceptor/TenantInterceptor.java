package com.ruoyi.framework.interceptor;

import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.framework.datasource.DynamicDataSourceContextHolder;
import com.ruoyi.framework.datasource.DynamicRoutingDataSource;
import com.ruoyi.tenant.domain.MasterTenant;
import com.ruoyi.tenant.domain.enums.TenantStatus;
import com.ruoyi.tenant.service.IMasterTenantService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;
import org.springframework.web.servlet.ModelAndView;

import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.util.HashMap;
import java.util.Map;

/**
 * 数据源拦截器
 *
 * @author devjd
 */

@Component
@Slf4j
public class TenantInterceptor implements HandlerInterceptor {

    @Autowired
    private IMasterTenantService masterTenantService;

    @Autowired
    private DynamicRoutingDataSource dynamicRoutingDataSource;

    @Value("${spring.datasource.driverClassName}")
    private String driverClassName;

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {

        String url = request.getServletPath();
        String tenant= request.getHeader("tenant");
        log.info("&&&&&&&&&&&&&&&& 租户拦截 &&&&&&&&&&&&&&&&");
        if (StringUtils.isNotBlank(tenant)) {
            if (!dynamicRoutingDataSource.existDataSource(tenant)) {
                //搜索默认数据库，去注册租户的数据源，下次进来直接session匹配数据源
                MasterTenant masterTenant = masterTenantService.selectMasterTenant(tenant);
                if (masterTenant == null) {
                    throw new RuntimeException("无此租户:"+tenant );
                }else if(TenantStatus.DISABLE.getCode().equals(masterTenant.getStatus())){
                    throw new RuntimeException("租户["+tenant+"]已停用" );
                }else if(masterTenant.getExpirationDate()!=null){
                    if(masterTenant.getExpirationDate().before(DateUtils.getNowDate())){
                        throw new RuntimeException("租户["+tenant+"]已过期");
                    }
                }
                Map<String, Object> map = new HashMap<>();
                map.put("driverClassName", driverClassName);
                map.put("url", masterTenant.getUrl());
                map.put("username", masterTenant.getUsername());
                map.put("password", masterTenant.getPassword());
                dynamicRoutingDataSource.addDataSource(tenant, map);

                log.info("&&&&&&&&&&& 已设置租户:{} 连接信息: {}", tenant, masterTenant);
            }else{
                log.info("&&&&&&&&&&& 当前租户:{}", tenant);
            }
        }else{
            throw new RuntimeException("缺少租户信息");
        }
        // 为了单次请求，多次连接数据库的情况，这里设置localThread，AbstractRoutingDataSource的方法去获取设置数据源
        DynamicDataSourceContextHolder.setDataSourceKey(tenant);
        return true;
    }

    @Override
    public void postHandle(HttpServletRequest request, HttpServletResponse response, Object handler,
                           ModelAndView modelAndView) throws Exception {
        // 请求结束删除localThread
        DynamicDataSourceContextHolder.clearDataSourceKey();
    }
}