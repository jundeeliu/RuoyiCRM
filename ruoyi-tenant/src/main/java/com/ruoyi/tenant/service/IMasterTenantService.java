package com.ruoyi.tenant.service;

import com.ruoyi.tenant.domain.MasterTenant;

/**
 * 参数配置 服务层
 * 
 * @author ruoyi
 */
public interface IMasterTenantService
{

     MasterTenant selectMasterTenant(String tenant);

}
