package com.ruoyi.crm.service.impl;

import java.util.Date;
import java.util.List;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.service.ICrmCustomerService;
import lombok.Data;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import com.ruoyi.crm.mapper.CrmCommentMapper;
import com.ruoyi.crm.domain.CrmComment;
import com.ruoyi.crm.service.ICrmCommentService;
import org.springframework.transaction.annotation.Transactional;

/**
 * 跟进记录Service业务层处理
 * 
 * @author ruoyi
 * @date 2022-01-18
 */
@Service
public class CrmCommentServiceImpl implements ICrmCommentService 
{
    @Autowired
    private CrmCommentMapper crmCommentMapper;

    @Autowired
    private ICrmCustomerService customerService;

    /**
     * 查询跟进记录
     * 
     * @param id 跟进记录主键
     * @return 跟进记录
     */
    @Override
    public CrmComment selectCrmCommentById(Long id)
    {
        return crmCommentMapper.selectCrmCommentById(id);
    }

    /**
     * 查询跟进记录列表
     * 
     * @param crmComment 跟进记录
     * @return 跟进记录
     */
    @Override
    public List<CrmComment> selectCrmCommentList(CrmComment crmComment)
    {
        return crmCommentMapper.selectCrmCommentList(crmComment);
    }

    /**
     * 新增跟进记录
     * 
     * @param crmComment 跟进记录
     * @return 结果
     */
    @Override
    public int insertCrmComment(CrmComment crmComment)
    {
        crmComment.setCreateTime(DateUtils.getNowDate());
        return crmCommentMapper.insertCrmComment(crmComment);
    }

    /**
     * 修改跟进记录
     * 
     * @param crmComment 跟进记录
     * @return 结果
     */
    @Override
    public int updateCrmComment(CrmComment crmComment)
    {
        crmComment.setUpdateTime(DateUtils.getNowDate());
        return crmCommentMapper.updateCrmComment(crmComment);
    }

    /**
     * 批量删除跟进记录
     * 
     * @param ids 需要删除的跟进记录主键
     * @return 结果
     */
    @Override
    public int deleteCrmCommentByIds(Long[] ids)
    {
        return crmCommentMapper.deleteCrmCommentByIds(ids);
    }

    /**
     * 删除跟进记录信息
     * 
     * @param id 跟进记录主键
     * @return 结果
     */
    @Override
    public int deleteCrmCommentById(Long id)
    {
        return crmCommentMapper.deleteCrmCommentById(id);
    }

    /**
     * 写跟进
     * @param crmComment 跟进
     * @param nextFollowupTime 下次跟进时间
     * @return
     */
    @Override
    @Transactional
    public int insertCrmComment(CrmComment crmComment, Date nextFollowupTime) {
        CrmCustomer crmCustomer = customerService.selectCrmCustomerById(crmComment.getCustomerId());
        crmCustomer.setLastUpdateRecord(crmComment.getContent());
        crmCustomer.setLastFollowupTime(DateUtils.getNowDate());
        crmCustomer.setNextFollowupTime(nextFollowupTime);
        customerService.updateCrmCustomer(crmCustomer);

        crmComment.setCreateTime(DateUtils.getNowDate());
        return crmCommentMapper.insertCrmComment(crmComment);
    }
}
