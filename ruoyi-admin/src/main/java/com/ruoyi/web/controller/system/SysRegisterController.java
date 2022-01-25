package com.ruoyi.web.controller.system;

import com.ruoyi.common.constant.TenantConstants;
import com.ruoyi.common.constant.UserConstants;
import com.ruoyi.framework.web.service.TenantRegisterService;
import com.ruoyi.tenant.dto.TenantDatabaseDTO;
import com.ruoyi.tenant.form.TenantRegisterForm;
import com.ruoyi.tenant.service.IMasterTenantService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;
import com.ruoyi.common.core.controller.BaseController;
import com.ruoyi.common.core.domain.AjaxResult;
import com.ruoyi.common.core.domain.model.RegisterBody;
import com.ruoyi.common.utils.StringUtils;
import com.ruoyi.framework.web.service.SysRegisterService;
import com.ruoyi.system.service.ISysConfigService;

import java.sql.SQLException;

/**
 * 注册验证
 * 
 * @author ruoyi
 */
@RestController
public class SysRegisterController extends BaseController
{
    @Autowired
    private SysRegisterService registerService;

    @Autowired
    private ISysConfigService configService;

    @Autowired
    private TenantRegisterService tenantRegisterService;

    @Autowired
    private IMasterTenantService masterTenantService;


    @PostMapping("/register")
    public AjaxResult registerTenant(@RequestBody TenantRegisterForm tenantRegisterForm){
        if (TenantConstants.NOT_UNIQUE.equals(masterTenantService.checkTenantNameUnique(tenantRegisterForm.tenantName)))
        {
            return AjaxResult.error("注册'" + tenantRegisterForm.getTenantName() + "'失败，账号已存在");
        }
        TenantDatabaseDTO tenantDatabase=null;
        try {
            tenantDatabase=tenantRegisterService.initDatabase(tenantRegisterForm);
        } catch (SQLException ex) {
            ex.printStackTrace();
            return AjaxResult.error("注册'" + tenantRegisterForm.getTenantName() + "'失败，创建租户时发生错误");
        }catch (Exception ex){
            ex.printStackTrace();
            return AjaxResult.error("注册'" + tenantRegisterForm.getTenantName() + "'失败，请与我们联系");
        }
        int i = masterTenantService.insertMasterTenant(tenantDatabase);
        return toAjax(i);
    }
}
