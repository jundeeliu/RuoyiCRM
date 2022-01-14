package com.ruoyi.crm.controller;

import java.util.List;
import javax.servlet.http.HttpServletResponse;

import com.ruoyi.crm.domain.enums.CustomerFolder;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.crm.domain.CrmCustomer;
import com.ruoyi.crm.service.ICrmCustomerService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 客户Controller
 * 
 * @author ruoyi
 * @date 2022-01-12
 */
@RestController
@RequestMapping("/crm/customer")
public class CrmCustomerController extends BaseController
{
    @Autowired
    private ICrmCustomerService crmCustomerService;

    /**
     * 查询我的客户列表
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:person:list')")
    @GetMapping("/person-list")
    public TableDataInfo personList(CrmCustomer crmCustomer)
    {
        startPage();
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        crmCustomer.setOwner(getUsername());
        List<CrmCustomer> list = crmCustomerService.selectCrmCustomerList(crmCustomer);
        return getDataTable(list);
    }

    /**
     * 查询客户列表
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:list')")
    @GetMapping("/list")
    public TableDataInfo list(CrmCustomer crmCustomer)
    {
        startPage();
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        List<CrmCustomer> list = crmCustomerService.selectCrmCustomerList(crmCustomer);
        return getDataTable(list);
    }

    /**
     * 导出客户列表
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:export')")
    @Log(title = "客户", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, CrmCustomer crmCustomer)
    {
        crmCustomer.setStatus(CustomerFolder.CUSTOMER.getCode());
        List<CrmCustomer> list = crmCustomerService.selectCrmCustomerList(crmCustomer);
        ExcelUtil<CrmCustomer> util = new ExcelUtil<CrmCustomer>(CrmCustomer.class);
        util.exportExcel(response, list, "客户数据");
    }

    /**
     * 获取客户详细信息
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id)
    {
        return AjaxResult.success(crmCustomerService.selectCrmCustomerById(id));
    }

    /**
     * 新增客户
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:add')")
    @Log(title = "客户", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CrmCustomer crmCustomer)
    {
        return toAjax(crmCustomerService.insertCrmCustomer(crmCustomer));
    }

    /**
     * 修改客户
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:edit')")
    @Log(title = "客户", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CrmCustomer crmCustomer)
    {
        return toAjax(crmCustomerService.updateCrmCustomer(crmCustomer));
    }

    /**
     * 删除客户
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:remove')")
    @Log(title = "客户", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids)
    {
        return toAjax(crmCustomerService.deleteCrmCustomerByIds(ids));
    }

    /**
     * 转移客户
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:transfer')")
    @Log(title = "客户", businessType = BusinessType.UPDATE)
    @PostMapping("/transfer")
    public AjaxResult transfer(@RequestParam("ids") Long[] ids, @RequestParam("owner") String newOwner){
        return toAjax(crmCustomerService.transferCrmCustomerByIds(ids, newOwner, getUsername()));
    }

     /**
     * 转入公海
     */
    @PreAuthorize("@ss.hasPermi('crm:customer:toPool')")
    @Log(title = "客户", businessType = BusinessType.UPDATE)
    @PostMapping("/to-pool")
    public AjaxResult toPool(@RequestParam("ids") Long[] ids, @RequestParam("poolType") String poolType){
        return toAjax(crmCustomerService.customerToPoolByIds(ids, poolType));
    }
}
