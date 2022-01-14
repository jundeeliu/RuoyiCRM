package com.ruoyi.crm.mapper;

import java.util.List;
import com.ruoyi.crm.domain.CrmCustomer;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 客户Mapper接口
 * 
 * @author ruoyi
 * @date 2022-01-12
 */
public interface CrmCustomerMapper
{
    /**
     * 查询客户
     * 
     * @param id 客户主键
     * @return 客户
     */
     CrmCustomer selectCrmCustomerById(Long id);

    /**
     * 查询客户列表
     * 
     * @param crmCustomer 客户
     * @return 客户集合
     */
     List<CrmCustomer> selectCrmCustomerList(CrmCustomer crmCustomer);

    /**
     * 新增客户
     * 
     * @param crmCustomer 客户
     * @return 结果
     */
     int insertCrmCustomer(CrmCustomer crmCustomer);

    /**
     * 修改客户
     * 
     * @param crmCustomer 客户
     * @return 结果
     */
     int updateCrmCustomer(CrmCustomer crmCustomer);

    /**
     * 删除客户
     * 
     * @param id 客户主键
     * @return 结果
     */
     int deleteCrmCustomerById(Long id);

    /**
     * 批量删除客户
     * 
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
     int deleteCrmCustomerByIds(Long[] ids);

    /**
     * 批量转移客户
     *
     * @param ids 需要转移的客户主键集合
     * @param newOwner 新负责人
     * @param oldOwner 原负责人
     * @return 结果
     */
    int transferCrmCustomerByIds(@Param("ids") Long[] ids,@Param("newOwner") String newOwner,@Param("oldOwner") String oldOwner);

    /**
     * 移入公海
     * @param ids 需要转移的客户主键集合
     * @param poolType 公海类型
     * @param status 状态码
     * @return
     */
    int customerToPoolByIds(@Param("ids") Long[] ids, @Param("poolType") String poolType, @Param("status") String status);
}
