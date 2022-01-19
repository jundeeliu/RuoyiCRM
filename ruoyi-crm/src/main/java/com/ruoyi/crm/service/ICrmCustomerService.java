package com.ruoyi.crm.service;

import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.vo.TodayUpdatesVO;

import java.util.List;

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
     * 移入公海
     * @param ids 需要转移的客户主键集合
     * @param poolType 公海类型
     * @return
     */
    int customerToPoolByIds(Long[] ids, String poolType);

    /**
     * 删除客户信息
     * 
     * @param id 客户主键
     * @return 结果
     */
     int deleteCrmCustomerById(Long id);


    /**
     * 领取客户
     * @param id 客户ID
     * @param owner 负责人
     * @return
     */
    int receiveCustomerById(Long id, String owner);

    /**
     * 今日动态
     * @param owner
     * @return
     */
    List<TodayUpdatesVO> todayUpdates(String owner);
}
