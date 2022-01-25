package com.ruoyi.tenant.domain;

import com.ruoyi.common.core.domain.BaseEntity;
import lombok.Data;

/**
 * @Author: devjd
 * @Date: 2021/7/25
 * @Description:
 */
@Data
public class MasterTenant extends BaseEntity {
    private Long id;
    private String tenant;
    private String url ;
    private String databaseName;
    private String username;
    private String password;
}
