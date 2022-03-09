package com.ruoyi.crm.controller;

import java.util.List;
import javax.servlet.http.HttpServletResponse;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.PutMapping;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.annotation.Log;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.enums.BusinessType;
import com.ruoyi.crm.domain.CrmOrder;
import com.ruoyi.crm.service.ICrmOrderService;
import com.ruoyi.common.utils.poi.ExcelUtil;
import com.ruoyi.common.core.page.TableDataInfo;

/**
 * 订单Controller
 * 
 * @author ruoyi
 * @date 2022-01-18
 */
@RestController
@RequestMapping("/crm/order")
public class CrmOrderController extends BaseController
{
    @Autowired
    private ICrmOrderService crmOrderService;

    /**
     * 查询订单列表
     */
    @PreAuthorize("@ss.hasPermi('crm:order:list')")
    @GetMapping("/list")
    public TableDataInfo list(CrmOrder crmOrder)
    {
        startPage();
        List<CrmOrder> list = crmOrderService.selectCrmOrderList(crmOrder);
        return getDataTable(list);
    }

    /**
     * 查询订单列表
     */
    @PreAuthorize("@ss.hasPermi('crm:order:person:list')")
    @GetMapping("/person-list")
    public TableDataInfo personList(CrmOrder crmOrder)
    {
        startPage();
        crmOrder.setOwner(getUsername());
        List<CrmOrder> list = crmOrderService.selectCrmOrderList(crmOrder);
        return getDataTable(list);
    }

    /**
     * 导出订单列表
     */
    @PreAuthorize("@ss.hasPermi('crm:order:export')")
    @Log(title = "订单", businessType = BusinessType.EXPORT)
    @PostMapping("/export")
    public void export(HttpServletResponse response, CrmOrder crmOrder)
    {
        List<CrmOrder> list = crmOrderService.selectCrmOrderList(crmOrder);
        ExcelUtil<CrmOrder> util = new ExcelUtil<CrmOrder>(CrmOrder.class);
        util.exportExcel(response, list, "订单数据");
    }

    /**
     * 获取订单详细信息
     */
    @PreAuthorize("@ss.hasPermi('crm:order:query')")
    @GetMapping(value = "/{id}")
    public AjaxResult getInfo(@PathVariable("id") Long id)
    {
        return AjaxResult.success(crmOrderService.selectCrmOrderById(id));
    }

    /**
     * 新增订单
     */
    @PreAuthorize("@ss.hasPermi('crm:order:add')")
    @Log(title = "订单", businessType = BusinessType.INSERT)
    @PostMapping
    public AjaxResult add(@RequestBody CrmOrder crmOrder)
    {
        crmOrder.setOwner(getUsername());
        crmOrder.setCreateBy(getUsername());
        return toAjax(crmOrderService.insertCrmOrder(crmOrder));
    }

    /**
     * 修改订单
     */
    @PreAuthorize("@ss.hasPermi('crm:order:edit')")
    @Log(title = "订单", businessType = BusinessType.UPDATE)
    @PutMapping
    public AjaxResult edit(@RequestBody CrmOrder crmOrder)
    {
        crmOrder.setUpdateBy(getUsername());
        return toAjax(crmOrderService.updateCrmOrder(crmOrder));
    }

    /**
     * 删除订单
     */
    @PreAuthorize("@ss.hasPermi('crm:order:remove')")
    @Log(title = "订单", businessType = BusinessType.DELETE)
	@DeleteMapping("/{ids}")
    public AjaxResult remove(@PathVariable Long[] ids)
    {
        return toAjax(crmOrderService.deleteCrmOrderByIds(ids));
    }

    /** 审批订单 */
    @PreAuthorize("@ss.hasPermi('crm:order:approve')")
    @Log(title = "订单", businessType = BusinessType.UPDATE)
    @PutMapping("/approve/{id}")
    public AjaxResult approve(@PathVariable Long id){

        return toAjax(crmOrderService.approve(id));
    }
}
