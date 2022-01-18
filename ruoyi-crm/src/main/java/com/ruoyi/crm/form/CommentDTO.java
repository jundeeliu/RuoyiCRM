package com.ruoyi.crm.form;

import lombok.Data;

import java.util.Date;

/**
 * @Author: devjd
 * @Date: 2022/1/18
 * @Description: 写跟进DTO
 */
@Data
public class CommentDTO {
    /** $column.columnComment */
    public Long id;

    /** 客户ID */
    public Long customerId;

    /** 回复内容 */
    public String content;

    /** 下次跟进时间 */
    public Date nextFollowupTime;
}
