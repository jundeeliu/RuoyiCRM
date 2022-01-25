package com.ruoyi.tenant.service.impl;

import com.ruoyi.common.annotation.DataSource;
import com.ruoyi.common.constant.TenantConstants;
import com.ruoyi.common.enums.DataSourceType;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.tenant.domain.MasterTenant;
import com.ruoyi.tenant.dto.TenantDatabaseDTO;
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

    @Override
    @DataSource(DataSourceType.MASTER)
    public int insertMasterTenant(TenantDatabaseDTO tenantDatabaseDTO){
        MasterTenant masterTenant = new MasterTenant();
        masterTenant.setTenant(tenantDatabaseDTO.getTenantName());
        masterTenant.setUrl(tenantDatabaseDTO.getUrl());
        masterTenant.setDatabaseName(tenantDatabaseDTO.getTenantDatabase());
        masterTenant.setUsername(tenantDatabaseDTO.getDbUser());
        masterTenant.setPassword(tenantDatabaseDTO.getDbPass());
        masterTenant.setCreateTime(DateUtils.getNowDate());
        return masterTenantMapper.insertMasterTenant(masterTenant);
    }

    @Override
    public String checkTenantNameUnique(String tenantName)
    {
        int count = masterTenantMapper.checkTenantNameUnique(tenantName);
        if (count > 0)
        {
            return TenantConstants.NOT_UNIQUE;
        }
        return TenantConstants.UNIQUE;
    }
}
