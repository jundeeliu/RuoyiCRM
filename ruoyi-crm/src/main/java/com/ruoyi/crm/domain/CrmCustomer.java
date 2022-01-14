package com.ruoyi.crm.domain;

import java.util.Date;
import com.fasterxml.jackson.annotation.JsonFormat;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseEntity;

/**
 * 客户对象 crm_customer
 *
 * @author devjd
 * @date 2022-01-13
 */
public class CrmCustomer extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    /** 客户ID */
    private Long id;

    /** 客户编号 */
    @Excel(name = "客户编号")
    private String code;

    /** 客户名称 */
    @Excel(name = "客户名称")
    private String name;

    /** 联系人 */
    @Excel(name = "联系人")
    private String linkman;

    /** 联系电话 */
    @Excel(name = "联系电话")
    private String phone;

    /** 地区 */
    @Excel(name = "地区")
    private String region;

    /** 客户行业 */
    @Excel(name = "客户行业")
    private String customerIndustry;

    /** 客户级别 */
    @Excel(name = "客户级别")
    private String customerRank;

    /** 客户状态 */
    @Excel(name = "客户状态")
    private String customerStatus;

    /** 状态(0线索 1客户 2公海) */
    private String status;

    /** 线索名称 */
    @Excel(name = "线索名称")
    private String cluesName;

    /** 线索来源 */
    @Excel(name = "线索来源")
    private String cluesSource;

    /** 线索状态 */
    @Excel(name = "线索状态")
    private String cluesStatus;

    /** 是否成交(0未成交 1成交) */
    private String dealStatus;

    /** 负责人 */
    @Excel(name = "负责人")
    private String owner;

    /** 删除标志(0代表存在 2代表删除) */
    private String delFlag;

    /** 版本 */
    private Long version;

    /** 最后跟进记录 */
    private String lastUpdateRecord;

    /** 最后跟进时间 */
    private Date lastFollowupTime;

    /** 下次跟进时间 */
    private Date nextFollowupTime;

    /** 前负责人 */
    private String preOwner;

    /** 转公海时间 */
    private Date toPoolTime;

    /** 转客户时间 */
    private Date toCustomerTime;

    /** 公海类型 */
    private String poolType;

    public void setId(Long id)
    {
        this.id = id;
    }

    public Long getId()
    {
        return id;
    }
    public void setCode(String code)
    {
        this.code = code;
    }

    public String getCode()
    {
        return code;
    }
    public void setName(String name)
    {
        this.name = name;
    }

    public String getName()
    {
        return name;
    }
    public void setLinkman(String linkman)
    {
        this.linkman = linkman;
    }

    public String getLinkman()
    {
        return linkman;
    }
    public void setPhone(String phone)
    {
        this.phone = phone;
    }

    public String getPhone()
    {
        return phone;
    }
    public void setRegion(String region)
    {
        this.region = region;
    }

    public String getRegion()
    {
        return region;
    }
    public void setCustomerIndustry(String customerIndustry)
    {
        this.customerIndustry = customerIndustry;
    }

    public String getCustomerIndustry()
    {
        return customerIndustry;
    }
    public void setCustomerRank(String customerRank)
    {
        this.customerRank = customerRank;
    }

    public String getCustomerRank()
    {
        return customerRank;
    }
    public void setCustomerStatus(String customerStatus)
    {
        this.customerStatus = customerStatus;
    }

    public String getCustomerStatus()
    {
        return customerStatus;
    }
    public void setStatus(String status)
    {
        this.status = status;
    }

    public String getStatus()
    {
        return status;
    }
    public void setCluesName(String cluesName)
    {
        this.cluesName = cluesName;
    }

    public String getCluesName()
    {
        return cluesName;
    }
    public void setCluesSource(String cluesSource)
    {
        this.cluesSource = cluesSource;
    }

    public String getCluesSource()
    {
        return cluesSource;
    }
    public void setCluesStatus(String cluesStatus)
    {
        this.cluesStatus = cluesStatus;
    }

    public String getCluesStatus()
    {
        return cluesStatus;
    }
    public void setDealStatus(String dealStatus)
    {
        this.dealStatus = dealStatus;
    }

    public String getDealStatus()
    {
        return dealStatus;
    }
    public void setOwner(String owner)
    {
        this.owner = owner;
    }

    public String getOwner()
    {
        return owner;
    }
    public void setDelFlag(String delFlag)
    {
        this.delFlag = delFlag;
    }

    public String getDelFlag()
    {
        return delFlag;
    }
    public void setVersion(Long version)
    {
        this.version = version;
    }

    public Long getVersion()
    {
        return version;
    }
    public void setLastUpdateRecord(String lastUpdateRecord)
    {
        this.lastUpdateRecord = lastUpdateRecord;
    }

    public String getLastUpdateRecord()
    {
        return lastUpdateRecord;
    }
    public void setLastFollowupTime(Date lastFollowupTime)
    {
        this.lastFollowupTime = lastFollowupTime;
    }

    public Date getLastFollowupTime()
    {
        return lastFollowupTime;
    }
    public void setNextFollowupTime(Date nextFollowupTime)
    {
        this.nextFollowupTime = nextFollowupTime;
    }

    public Date getNextFollowupTime()
    {
        return nextFollowupTime;
    }
    public void setPreOwner(String preOwner)
    {
        this.preOwner = preOwner;
    }

    public String getPreOwner()
    {
        return preOwner;
    }
    public void setToPoolTime(Date toPoolTime)
    {
        this.toPoolTime = toPoolTime;
    }

    public Date getToPoolTime()
    {
        return toPoolTime;
    }
    public void setToCustomerTime(Date toCustomerTime)
    {
        this.toCustomerTime = toCustomerTime;
    }

    public Date getToCustomerTime()
    {
        return toCustomerTime;
    }
    public void setPoolType(String poolType)
    {
        this.poolType = poolType;
    }

    public String getPoolType()
    {
        return poolType;
    }

    @Override
    public String toString() {
        return new ToStringBuilder(this,ToStringStyle.MULTI_LINE_STYLE)
                .append("id", getId())
                .append("code", getCode())
                .append("name", getName())
                .append("linkman", getLinkman())
                .append("phone", getPhone())
                .append("region", getRegion())
                .append("customerIndustry", getCustomerIndustry())
                .append("customerRank", getCustomerRank())
                .append("customerStatus", getCustomerStatus())
                .append("status", getStatus())
                .append("cluesName", getCluesName())
                .append("cluesSource", getCluesSource())
                .append("cluesStatus", getCluesStatus())
                .append("dealStatus", getDealStatus())
                .append("owner", getOwner())
                .append("delFlag", getDelFlag())
                .append("version", getVersion())
                .append("createBy", getCreateBy())
                .append("createTime", getCreateTime())
                .append("updateBy", getUpdateBy())
                .append("updateTime", getUpdateTime())
                .append("remark", getRemark())
                .append("lastUpdateRecord", getLastUpdateRecord())
                .append("lastFollowupTime", getLastFollowupTime())
                .append("nextFollowupTime", getNextFollowupTime())
                .append("preOwner", getPreOwner())
                .append("toPoolTime", getToPoolTime())
                .append("toCustomerTime", getToCustomerTime())
                .append("poolType", getPoolType())
                .toString();
    }
}
