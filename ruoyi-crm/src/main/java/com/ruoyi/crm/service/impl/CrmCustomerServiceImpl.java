package com.ruoyi.crm.service.impl;

import java.util.List;
import com.ruoyi.common.utils.DateUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.crm.mapper.CrmCustomerMapper;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.service.ICrmCustomerService;
import org.springframework.transaction.annotation.Transactional;

/**
 * 客户Service业务层处理
 * 
 * @author ruoyi
 * @date 2022-01-12
 */
@Service
public class CrmCustomerServiceImpl implements ICrmCustomerService 
{
    @Autowired
    private CrmCustomerMapper crmCustomerMapper;

    /**
     * 查询客户
     * 
     * @param id 客户主键
     * @return 客户
     */
    @Override
    public CrmCustomer selectCrmCustomerById(Long id)
    {
        return crmCustomerMapper.selectCrmCustomerById(id);
    }

    /**
     * 查询客户列表
     * 
     * @param crmCustomer 客户
     * @return 客户
     */
    @Override
    public List<CrmCustomer> selectCrmCustomerList(CrmCustomer crmCustomer)
    {
        return crmCustomerMapper.selectCrmCustomerList(crmCustomer);
    }

    /**
     * 新增客户
     * 
     * @param crmCustomer 客户
     * @return 结果
     */
    @Override
    public int insertCrmCustomer(CrmCustomer crmCustomer)
    {
        crmCustomer.setCreateTime(DateUtils.getNowDate());
        return crmCustomerMapper.insertCrmCustomer(crmCustomer);
    }

    /**
     * 修改客户
     * 
     * @param crmCustomer 客户
     * @return 结果
     */
    @Override
    public int updateCrmCustomer(CrmCustomer crmCustomer)
    {
        crmCustomer.setUpdateTime(DateUtils.getNowDate());
        return crmCustomerMapper.updateCrmCustomer(crmCustomer);
    }

    /**
     * 批量删除客户
     * 
     * @param ids 需要删除的客户主键
     * @return 结果
     */
    @Override
    public int deleteCrmCustomerByIds(Long[] ids)
    {
        return crmCustomerMapper.deleteCrmCustomerByIds(ids);
    }

    @Override
    @Transactional
    public int transferCrmCustomerByIds(Long[] ids, String newOwner, String oldOwner) {
        return crmCustomerMapper.transferCrmCustomerByIds(ids, newOwner, oldOwner);
    }

    /**
     * 删除客户信息
     * 
     * @param id 客户主键
     * @return 结果
     */
    @Override
    public int deleteCrmCustomerById(Long id)
    {
        return crmCustomerMapper.deleteCrmCustomerById(id);
    }
}
