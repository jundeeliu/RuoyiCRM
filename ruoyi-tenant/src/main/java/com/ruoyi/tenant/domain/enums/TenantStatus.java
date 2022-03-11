package com.ruoyi.tenant.domain.enums;

/**
 * 租户状态
 * 
 * @author devjd
 */
public enum TenantStatus
{
    NORMAL("1", "正常"), DISABLE("2", "停用");

    private final String code;
    private final String info;

    TenantStatus(String code, String info)
    {
        this.code = code;
        this.info = info;
    }

    public String getCode()
    {
        return code;
    }

    public String getInfo()
    {
        return info;
    }
}