package com.ruoyi.crm.service;

import java.util.List;
import com.ruoyi.crm.domain.CrmCustomer;

/**
 * 客户Service接口
 * 
 * @author devjd
 * @date 2022-01-12
 */
 public interface ICrmCustomerService
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
     * 批量删除客户
     * 
     * @param ids 需要删除的客户主键集合
     * @return 结果
     */
     int deleteCrmCustomerByIds(Long[] ids);


    /**
     * 批量转移客户
     *
     * @param ids 需要转移的客户主键集合
     * @param newOwner 新负责人
     * @param oldOwner 旧负责人
     * @return 结果
     */
    int transferCrmCustomerByIds(Long[] ids, String newOwner, String oldOwner);

    /**
     * 删除客户信息
     * 
     * @param id 客户主键
     * @return 结果
     */
     int deleteCrmCustomerById(Long id);
}
