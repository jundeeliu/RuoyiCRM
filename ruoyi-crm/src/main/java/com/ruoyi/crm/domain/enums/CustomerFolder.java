package com.ruoyi.crm.domain.enums;

/**
 * 客户状态
 * 
 * @author ruoyi
 */
public enum CustomerFolder
{
    CLUES("0", "线索"), CUSTOMER("1", "客户"), POOL("2", "公海");

    private final String code;
    private final String info;

    CustomerFolder(String code, String info)
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
