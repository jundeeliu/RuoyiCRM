package com.ruoyi.framework.aspectj;

import java.util.ArrayList;
import java.util.List;
import org.aspectj.lang.JoinPoint;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.springframework.stereotype.Component;
import com.ruoyi.common.annotation.DataScope;
import com.ruoyi.common.constant.UserConstants;
import com.ruoyi.common.core.domain.BaseEntity;
import com.ruoyi.common.core.domain.DataScopeCriteria;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.common.utils.SecurityUtils;

/** Builds a typed data-scope decision for the five list queries. */
@Aspect
@Component
public class DataScopeAspect
{
    public static final String DATA_SCOPE_ALL = "1";
    public static final String DATA_SCOPE_CUSTOM = "2";
    public static final String DATA_SCOPE_DEPT = "3";
    public static final String DATA_SCOPE_DEPT_AND_CHILD = "4";
    public static final String DATA_SCOPE_SELF = "5";

    @Before("@annotation(controllerDataScope)")
    public void doBefore(JoinPoint point, DataScope controllerDataScope)
    {
        BaseEntity entity = entityArgument(point);
        entity.getParams().remove("dataScope");
        entity.getParams().remove("dataScopeCriteria");
        entity.applyDataScope(DataScopeCriteria.denied());

        LoginUser loginUser = SecurityUtils.getLoginUser();
        SysUser user = loginUser == null ? null : loginUser.getUser();
        if (user == null)
        {
            return;
        }
        if (user.isAdmin())
        {
            entity.applyDataScope(DataScopeCriteria.unrestricted());
            return;
        }
        dataScopeFilter(point, user, controllerDataScope.deptAlias(), controllerDataScope.userAlias());
    }

    /**
     * Public for existing callers and focused tests. Unknown aliases or role
     * scopes are denied; aliases never reach SQL as interpolated identifiers.
     */
    public static void dataScopeFilter(JoinPoint joinPoint, SysUser user, String deptAlias, String userAlias)
    {
        BaseEntity entity = entityArgument(joinPoint);
        entity.applyDataScope(DataScopeCriteria.denied());
        if (user == null || !"d".equals(deptAlias) || !("u".equals(userAlias) || "".equals(userAlias)))
        {
            return;
        }

        List<Long> roleIds = new ArrayList<>();
        boolean includeDepartment = false;
        boolean includeChildren = false;
        boolean includeSelf = false;
        List<SysRole> roles = user.getRoles();
        if (roles == null)
        {
            return;
        }
        for (SysRole role : roles)
        {
            if (role == null || !UserConstants.NORMAL.equals(role.getStatus()))
            {
                continue;
            }
            String scope = role.getDataScope();
            if (DATA_SCOPE_ALL.equals(scope))
            {
                entity.applyDataScope(DataScopeCriteria.unrestricted());
                return;
            }
            if (DATA_SCOPE_CUSTOM.equals(scope))
            {
                roleIds.add(role.getRoleId());
            }
            else if (DATA_SCOPE_DEPT.equals(scope))
            {
                includeDepartment = true;
            }
            else if (DATA_SCOPE_DEPT_AND_CHILD.equals(scope))
            {
                includeChildren = true;
            }
            else if (DATA_SCOPE_SELF.equals(scope) && "u".equals(userAlias))
            {
                includeSelf = true;
            }
        }
        entity.applyDataScope(DataScopeCriteria.restricted(roleIds, user.getDeptId(), user.getUserId(),
                includeDepartment, includeChildren, includeSelf));
    }

    private static BaseEntity entityArgument(JoinPoint point)
    {
        if (point == null || point.getArgs() == null || point.getArgs().length == 0
                || !(point.getArgs()[0] instanceof BaseEntity))
        {
            throw new IllegalArgumentException("@DataScope requires a BaseEntity first argument");
        }
        return (BaseEntity) point.getArgs()[0];
    }
}
