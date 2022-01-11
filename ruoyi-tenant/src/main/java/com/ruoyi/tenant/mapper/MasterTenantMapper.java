package com.ruoyi.tenant.mapper;

import java.util.List;
import com.ruoyi.tenant.domain.MasterTenant;
import org.apache.ibatis.annotations.Mapper;

/**
 * 参数配置 数据层
 * 
 * @author ruoyi
 */
@Mapper
public interface MasterTenantMapper
{

     MasterTenant selectMasterTenant(MasterTenant masterTenant);


     List<MasterTenant> selectMasterTenantList(MasterTenant masterTenant);
}
