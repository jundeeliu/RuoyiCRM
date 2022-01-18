package com.ruoyi.crm.mapper;

import java.util.List;
import com.ruoyi.crm.domain.CrmComment;

/**
 * 跟进记录Mapper接口
 * 
 * @author ruoyi
 * @date 2022-01-18
 */
 public interface CrmCommentMapper
{
    /**
     * 查询跟进记录
     * 
     * @param id 跟进记录主键
     * @return 跟进记录
     */
     CrmComment selectCrmCommentById(Long id);

    /**
     * 查询跟进记录列表
     * 
     * @param crmComment 跟进记录
     * @return 跟进记录集合
     */
     List<CrmComment> selectCrmCommentList(CrmComment crmComment);

    /**
     * 新增跟进记录
     * 
     * @param crmComment 跟进记录
     * @return 结果
     */
     int insertCrmComment(CrmComment crmComment);

    /**
     * 修改跟进记录
     * 
     * @param crmComment 跟进记录
     * @return 结果
     */
     int updateCrmComment(CrmComment crmComment);

    /**
     * 删除跟进记录
     * 
     * @param id 跟进记录主键
     * @return 结果
     */
     int deleteCrmCommentById(Long id);

    /**
     * 批量删除跟进记录
     * 
     * @param ids 需要删除的数据主键集合
     * @return 结果
     */
     int deleteCrmCommentByIds(Long[] ids);
}
