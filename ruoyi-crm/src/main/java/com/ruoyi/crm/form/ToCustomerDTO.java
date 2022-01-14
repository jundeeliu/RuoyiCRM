package com.ruoyi.crm.form;

import lombok.Data;

/**
 * @Author: devjd
 * @Date: 2022/1/14
 * @Description: 转化成客的DTO
 */
@Data
public class ToCustomerDTO {
    public Long id;
    public String name;
    public String customerStatus;
    public String customerRank;
}
