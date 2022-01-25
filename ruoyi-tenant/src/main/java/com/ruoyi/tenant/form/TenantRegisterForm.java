package com.ruoyi.tenant.form;

import lombok.Data;

/**
 * @Author: eddie
 * @Date: 2022/1/22
 * @Description:
 */
@Data
public class TenantRegisterForm {
    /** 租户ID，唯一 */
    public String tenantName;

    /** 管理员用户名 */
    public String adminName;

    /** 管理员密码 */
    public String adminPass;

}
