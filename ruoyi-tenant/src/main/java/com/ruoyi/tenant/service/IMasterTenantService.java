package com.ruoyi.tenant.service;

import com.ruoyi.tenant.domain.MasterTenant;
import com.ruoyi.tenant.dto.TenantDatabaseDTO;

/**
 * 参数配置 服务层
 * 
 * @author ruoyi
 */
public interface IMasterTenantService
{

     MasterTenant selectMasterTenant(String tenant);

    int insertMasterTenant(TenantDatabaseDTO tenantDatabaseDTO);

    String checkTenantNameUnique(String tenantName);
}
