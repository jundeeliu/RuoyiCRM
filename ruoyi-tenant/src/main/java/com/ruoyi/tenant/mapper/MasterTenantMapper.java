package com.ruoyi.tenant.mapper;

import java.util.List;
import com.ruoyi.tenant.domain.MasterTenant;
import org.apache.ibatis.annotations.Mapper;

/**
 * 租户
 * 
 * @author ruoyi
 */
@Mapper
public interface MasterTenantMapper
{

     MasterTenant selectMasterTenant(MasterTenant masterTenant);

     /**
      * 新增租户
      *
      * @param masterTenant 租户数据库连接信息
      * @return 结果
      */
     int insertMasterTenant(MasterTenant masterTenant);


     List<MasterTenant> selectMasterTenantList(MasterTenant masterTenant);

    int checkTenantNameUnique(String tenantName);
}
