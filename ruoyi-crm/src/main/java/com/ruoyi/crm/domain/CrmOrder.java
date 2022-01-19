package com.ruoyi.crm.domain;

import java.math.BigDecimal;
import org.apache.commons.lang3.builder.ToStringBuilder;
import org.apache.commons.lang3.builder.ToStringStyle;
import com.ruoyi.common.annotation.Excel;
import com.ruoyi.common.core.domain.BaseEntity;
import org.springframework.data.annotation.Transient;

/**
 * 订单对象 crm_order
 * 
 * @author devjd
 * @date 2022-01-18
 */
public class CrmOrder extends BaseEntity
{
    private static final long serialVersionUID = 1L;

    /** $column.columnComment */
    private Long id;

    /** 订单编号 */
    @Excel(name = "订单编号")
    private String orderNo;

    /** 客户ID */
    @Excel(name = "客户ID")
    private Long customerId;

    /** 订单金额 */
    @Excel(name = "订单金额")
    private BigDecimal amount;

    /** 负责人 */
    @Excel(name = "负责人")
    private String owner;

    /** 状态(0待审核 1审核通过 2审核不通过) */
    @Excel(name = "状态(0待审核 1审核通过 2审核不通过)")
    private String status;

    @Excel(name="客户名称")
    @Transient
    private String customerName;

    public Long getId() {
        return id;
    }

    public void setId(Long id) {
        this.id = id;
    }

    public String getOrderNo() {
        return orderNo;
    }

    public void setOrderNo(String orderNo) {
        this.orderNo = orderNo;
    }

    public Long getCustomerId() {
        return customerId;
    }

    public void setCustomerId(Long customerId) {
        this.customerId = customerId;
    }

    public BigDecimal getAmount() {
        return amount;
    }

    public void setAmount(BigDecimal amount) {
        this.amount = amount;
    }

    public String getOwner() {
        return owner;
    }

    public void setOwner(String owner) {
        this.owner = owner;
    }

    public String getStatus() {
        return status;
    }

    public void setStatus(String status) {
        this.status = status;
    }

    public String getCustomerName() {
        return customerName;
    }

    public void setCustomerName(String customerName) {
        this.customerName = customerName;
    }

    @Override
    public String toString() {
        return "CrmOrder{" +
                "id=" + id +
                ", orderNo='" + orderNo + '\'' +
                ", customerId=" + customerId +
                ", amount=" + amount +
                ", owner='" + owner + '\'' +
                ", status='" + status + '\'' +
                ", customerName='" + customerName + '\'' +
                '}';
    }
}
