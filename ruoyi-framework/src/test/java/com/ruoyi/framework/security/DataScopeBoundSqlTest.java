package com.ruoyi.framework.security;

import static org.junit.jupiter.api.Assertions.assertFalse;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertTrue;
import static org.mockito.Mockito.mock;
import static org.mockito.Mockito.when;

import com.ruoyi.common.annotation.DataScope;
import com.ruoyi.common.core.domain.BaseEntity;
import com.ruoyi.common.core.domain.DataScopeCriteria;
import com.ruoyi.common.core.domain.entity.SysDept;
import com.ruoyi.common.core.domain.entity.SysRole;
import com.ruoyi.common.core.domain.entity.SysUser;
import com.ruoyi.common.core.domain.model.LoginUser;
import com.ruoyi.framework.aspectj.DataScopeAspect;
import java.io.InputStream;
import java.util.List;
import org.apache.ibatis.builder.xml.XMLMapperBuilder;
import org.apache.ibatis.mapping.BoundSql;
import org.apache.ibatis.session.Configuration;
import org.aspectj.lang.JoinPoint;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.beans.MutablePropertyValues;
import org.springframework.web.bind.WebDataBinder;

class DataScopeBoundSqlTest
{
    private static final String USER = "com.ruoyi.system.mapper.SysUserMapper.";
    private static final String ROLE = "com.ruoyi.system.mapper.SysRoleMapper.";
    private static final String DEPT = "com.ruoyi.system.mapper.SysDeptMapper.";

    @AfterEach
    void clearContext()
    {
        SecurityContextHolder.clearContext();
    }

    @Test
    void clientForgedParamsCannotBroadenAnyOfFiveQueries() throws Exception
    {
        Configuration configuration = mapperConfiguration();
        for (String id : List.of(USER + "selectUserList", USER + "selectAllocatedList",
                USER + "selectUnallocatedList", ROLE + "selectRoleList", DEPT + "selectDeptList"))
        {
            BaseEntity query = id.startsWith(USER) ? new SysUser()
                    : id.startsWith(ROLE) ? new SysRole() : new SysDept();
            query.getParams().put("dataScope", " OR 1=1 --");
            query.getParams().put("dataScopeCriteria", java.util.Map.of("unrestricted", true));
            BoundSql sql = configuration.getMappedStatement(id).getBoundSql(query);
            assertTrue(sql.getSql().contains("AND 1 = 0"), id);
            assertFalse(sql.getSql().contains("OR 1=1"), id);
        }
    }

    @Test
    void aspectReplacesForgedParamsAndBindsRoleDepartmentAndUserValues() throws Exception
    {
        SysUser query = new SysUser();
        query.getParams().put("dataScope", " OR 1=1 --");
        query.getParams().put("dataScopeCriteria", java.util.Map.of("unrestricted", true));
        SysRole custom = role(17L, DataScopeAspect.DATA_SCOPE_CUSTOM, "0");
        SysRole department = role(18L, DataScopeAspect.DATA_SCOPE_DEPT_AND_CHILD, "0");
        SysRole self = role(19L, DataScopeAspect.DATA_SCOPE_SELF, "0");
        SysUser current = user(9L, 4L, List.of(custom, department, self));
        LoginUser login = new LoginUser();
        login.setUser(current);
        login.setTenant("tenant-a");
        SecurityContextHolder.getContext().setAuthentication(
                new UsernamePasswordAuthenticationToken(login, null, List.of()));
        JoinPoint point = point(query);
        DataScope annotation = mock(DataScope.class);
        when(annotation.deptAlias()).thenReturn("d");
        when(annotation.userAlias()).thenReturn("u");

        new DataScopeAspect().doBefore(point, annotation);

        assertFalse(query.getParams().containsKey("dataScope"));
        assertFalse(query.getParams().containsKey("dataScopeCriteria"));
        DataScopeCriteria criteria = query.getDataScopeCriteria();
        assertNotNull(criteria);
        assertFalse(criteria.isDenied());
        BoundSql sql = mapperConfiguration().getMappedStatement(USER + "selectUserList").getBoundSql(query);
        assertTrue(sql.getSql().contains("sys_role_dept"));
        assertTrue(sql.getSql().contains("find_in_set"));
        assertTrue(sql.getSql().contains("u.user_id = ?"));
        assertFalse(sql.getSql().contains("OR 1=1"));
        assertTrue(sql.getParameterMappings().stream()
                .anyMatch(mapping -> mapping.getProperty().contains("dataScopeCriteria.deptId")));
        assertTrue(sql.getParameterMappings().stream()
                .anyMatch(mapping -> mapping.getProperty().contains("dataScopeCriteria.userId")));
    }

    @Test
    void inactiveOrUnknownRolesAndUnknownAliasesDenyRows()
    {
        SysUser query = new SysUser();
        SysUser current = user(9L, 4L, List.of(
                role(1L, DataScopeAspect.DATA_SCOPE_ALL, "1"),
                role(2L, "UNKNOWN", "0")));
        DataScopeAspect.dataScopeFilter(point(query), current, "d", "u");
        assertTrue(query.getDataScopeCriteria().isDenied());

        current.setRoles(List.of(role(3L, DataScopeAspect.DATA_SCOPE_ALL, "0")));
        DataScopeAspect.dataScopeFilter(point(query), current, "injected_alias", "u");
        assertTrue(query.getDataScopeCriteria().isDenied());
    }

    @Test
    void httpJsonCannotPopulateServerOwnedCriteria() throws Exception
    {
        com.fasterxml.jackson.databind.ObjectMapper mapper = new com.fasterxml.jackson.databind.ObjectMapper();
        SysUser query = mapper.readValue("{\"params\":{\"dataScope\":\" OR 1=1 --\"},"
                + "\"dataScopeCriteria\":{\"unrestricted\":true}}", SysUser.class);
        assertTrue(query.getDataScopeCriteria().isDenied());
    }

    @Test
    void formBindingCannotPopulateServerOwnedCriteria()
    {
        SysUser query = new SysUser();
        WebDataBinder binder = new WebDataBinder(query);
        MutablePropertyValues values = new MutablePropertyValues();
        values.add("dataScopeCriteria.unrestricted", "true");
        values.add("params[dataScope]", " OR 1=1 --");
        values.add("params[dataScopeCriteria]", "unrestricted");
        binder.bind(values);

        assertTrue(query.getDataScopeCriteria().isDenied());
        BoundSql sql = org.junit.jupiter.api.Assertions.assertDoesNotThrow(() -> mapperConfiguration()
                .getMappedStatement(USER + "selectUserList").getBoundSql(query));
        assertTrue(sql.getSql().contains("AND 1 = 0"));
    }

    private static Configuration mapperConfiguration() throws Exception
    {
        Configuration configuration = new Configuration();
        configuration.getTypeAliasRegistry().registerAlias("SysUser", SysUser.class);
        configuration.getTypeAliasRegistry().registerAlias("SysRole", SysRole.class);
        configuration.getTypeAliasRegistry().registerAlias("SysDept", SysDept.class);
        for (String resource : List.of("mapper/system/SysUserMapper.xml", "mapper/system/SysRoleMapper.xml",
                "mapper/system/SysDeptMapper.xml"))
        {
            try (InputStream input = DataScopeBoundSqlTest.class.getClassLoader().getResourceAsStream(resource))
            {
                assertNotNull(input, resource);
                new XMLMapperBuilder(input, configuration, resource, configuration.getSqlFragments()).parse();
            }
        }
        return configuration;
    }

    private static JoinPoint point(BaseEntity entity)
    {
        JoinPoint point = mock(JoinPoint.class);
        when(point.getArgs()).thenReturn(new Object[] { entity });
        return point;
    }

    private static SysRole role(Long id, String scope, String status)
    {
        SysRole role = new SysRole();
        role.setRoleId(id);
        role.setDataScope(scope);
        role.setStatus(status);
        return role;
    }

    private static SysUser user(Long id, Long deptId, List<SysRole> roles)
    {
        SysUser user = new SysUser();
        user.setUserId(id);
        user.setDeptId(deptId);
        user.setRoles(roles);
        return user;
    }
}
