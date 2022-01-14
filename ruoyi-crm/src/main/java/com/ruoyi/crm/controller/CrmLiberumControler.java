package com.ruoyi.crm.controller;

import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.page.TableDataInfo;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.domain.enums.CustomerFolder;
import com.ruoyi.crm.service.ICrmCustomerService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import javax.servlet.http.HttpServletResponse;
import java.util.List;

/**
 * 公海管理Controller
 * 
 * @author devjd
 * @date 2022-01-12
 */
@RestController
@RequestMapping("/crm/liberum")
public class CrmLiberumControler extends BaseController
{
    @Autowired
    private ICrmCustomerService crmCustomerService;

    /**
     * 查询客户列表
     */
    @PreAuthorize("@ss.hasPermi('crm:liberum:list')")
    @GetMapping("/list")
    public TableDataInfo list(CrmCustomer crmCustomer)
    {
        startPage();
        crmCustomer.setStatus(CustomerFolder.LIBERUM.getCode());
        List<CrmCustomer> list = crmCustomerService.selectCrmCustomerList(crmCustomer);
        return getDataTable(list);
    }


    /**
     * 获取客户详细信息
     */
    @PreAuthorize("@ss.hasPermi('crm:liberum:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id)
    {
        return AjaxResult.success(crmCustomerService.selectCrmCustomerById(id));
    }

}
