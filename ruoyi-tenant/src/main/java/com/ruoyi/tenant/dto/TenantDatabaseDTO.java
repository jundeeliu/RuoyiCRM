package com.ruoyi.tenant.dto;

import lombok.Data;

/**
 * @Author: eddie
 * @Date: 2022/1/22
 * @Description:
 */
@Data
public class TenantDatabaseDTO {
    public String tenantDatabase;
    public String dbUser;
    public String dbPass;
    public String adminName;
    public String adminPass;
    public String tenantName;
    public String url;
}
