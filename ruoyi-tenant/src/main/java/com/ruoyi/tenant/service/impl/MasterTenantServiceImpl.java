package com.ruoyi.tenant.service.impl;

import com.ruoyi.common.annotation.DataSource;
import com.ruoyi.common.enums.DataSourceType;
import com.ruoyi.tenant.domain.MasterTenant;
import com.ruoyi.tenant.mapper.MasterTenantMapper;
import com.ruoyi.tenant.service.IMasterTenantService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

/**
 * @Author: eddie
 * @Date: 2021/7/25
 * @Description:
 */
@Service
public class MasterTenantServiceImpl implements IMasterTenantService {

    @Autowired
    private MasterTenantMapper masterTenantMapper;

    @Override
    @DataSource(DataSourceType.MASTER)
    public MasterTenant selectMasterTenant(String tenant) {
        MasterTenant masterTenant = new MasterTenant();
        masterTenant.setTenant(tenant);
        return masterTenantMapper.selectMasterTenant(masterTenant);
    }
}
