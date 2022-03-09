package com.ruoyi.crm.service.impl;

import java.util.List;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.domain.enums.CustomerFolder;
import com.ruoyi.crm.service.ICrmCustomerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.crm.mapper.CrmOrderMapper;
import com.ruoyi.crm.domain.CrmOrder;
import com.ruoyi.crm.service.ICrmOrderService;
import org.springframework.transaction.annotation.Transactional;

/**
 * 订单Service业务层处理
 * 
 * @author ruoyi
 * @date 2022-01-18
 */
@Service
public class CrmOrderServiceImpl implements ICrmOrderService 
{
    @Autowired
    private CrmOrderMapper crmOrderMapper;

    @Autowired
    private ICrmCustomerService customerService;

    /**
     * 查询订单
     * 
     * @param id 订单主键
     * @return 订单
     */
    @Override
    public CrmOrder selectCrmOrderById(Long id)
    {
        return crmOrderMapper.selectCrmOrderById(id);
    }

    /**
     * 查询订单列表
     * 
     * @param crmOrder 订单
     * @return 订单
     */
    @Override
    public List<CrmOrder> selectCrmOrderList(CrmOrder crmOrder)
    {
        return crmOrderMapper.selectCrmOrderList(crmOrder);
    }

    /**
     * 新增订单
     * 
     * @param crmOrder 订单
     * @return 结果
     */
    @Override
    public int insertCrmOrder(CrmOrder crmOrder)
    {
        crmOrder.setCreateTime(DateUtils.getNowDate());
        return crmOrderMapper.insertCrmOrder(crmOrder);
    }

    /**
     * 修改订单
     * 
     * @param crmOrder 订单
     * @return 结果
     */
    @Override
    public int updateCrmOrder(CrmOrder crmOrder)
    {
        crmOrder.setUpdateTime(DateUtils.getNowDate());
        return crmOrderMapper.updateCrmOrder(crmOrder);
    }

    /**
     * 批量删除订单
     * 
     * @param ids 需要删除的订单主键
     * @return 结果
     */
    @Override
    public int deleteCrmOrderByIds(Long[] ids)
    {
        return crmOrderMapper.deleteCrmOrderByIds(ids);
    }

    /**
     * 删除订单信息
     * 
     * @param id 订单主键
     * @return 结果
     */
    @Override
    public int deleteCrmOrderById(Long id)
    {
        return crmOrderMapper.deleteCrmOrderById(id);
    }

    /** 审核订单 */
    @Transactional
    @Override
    public int approve(Long id) {
        CrmOrder crmOrder = crmOrderMapper.selectCrmOrderById(id);
        crmOrder.setStatus("1");

        CrmCustomer crmCustomer = customerService.selectCrmCustomerById(crmOrder.getCustomerId());
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        crmCustomer.setDealStatus("1");
        customerService.updateCrmCustomer(crmCustomer);
        return crmOrderMapper.updateCrmOrder(crmOrder);
    }
}
