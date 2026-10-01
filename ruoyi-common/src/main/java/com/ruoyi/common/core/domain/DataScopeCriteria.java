package com.ruoyi.common.core.domain;

import java.util.List;

/**
 * Server-created, immutable data-scope decisions. All values reach MyBatis via
 * bound parameters; no SQL text or column names are supplied by a request.
 */
public final class DataScopeCriteria
{
    private static final DataScopeCriteria DENIED = new DataScopeCriteria(false, true,
            List.of(), null, null, false, false, false);
    private static final DataScopeCriteria UNRESTRICTED = new DataScopeCriteria(true, false,
            List.of(), null, null, false, false, false);

    private final boolean unrestricted;
    private final boolean denied;
    private final List<Long> roleIds;
    private final Long deptId;
    private final Long userId;
    private final boolean includeDepartment;
    private final boolean includeChildren;
    private final boolean includeSelf;

    private DataScopeCriteria(boolean unrestricted, boolean denied, List<Long> roleIds,
            Long deptId, Long userId, boolean includeDepartment, boolean includeChildren,
            boolean includeSelf)
    {
        this.unrestricted = unrestricted;
        this.denied = denied;
        this.roleIds = List.copyOf(roleIds);
        this.deptId = deptId;
        this.userId = userId;
        this.includeDepartment = includeDepartment;
        this.includeChildren = includeChildren;
        this.includeSelf = includeSelf;
    }

    public static DataScopeCriteria denied()
    {
        return DENIED;
    }

    public static DataScopeCriteria unrestricted()
    {
        return UNRESTRICTED;
    }

    public static DataScopeCriteria restricted(List<Long> roleIds, Long deptId, Long userId,
            boolean includeDepartment, boolean includeChildren, boolean includeSelf)
    {
        List<Long> validRoles = roleIds == null ? List.of() : roleIds.stream()
                .filter(id -> id != null && id > 0).distinct().toList();
        boolean validDept = deptId != null && deptId > 0;
        boolean validUser = userId != null && userId > 0;
        boolean dept = includeDepartment && validDept;
        boolean children = includeChildren && validDept;
        boolean self = includeSelf && validUser;
        if (validRoles.isEmpty() && !dept && !children && !self)
        {
            return DENIED;
        }
        return new DataScopeCriteria(false, false, validRoles,
                validDept ? deptId : null, validUser ? userId : null, dept, children, self);
    }

    public boolean isUnrestricted() { return unrestricted; }
    public boolean isDenied() { return denied; }
    public List<Long> getRoleIds() { return roleIds; }
    public Long getDeptId() { return deptId; }
    public Long getUserId() { return userId; }
    public boolean isIncludeDepartment() { return includeDepartment; }
    public boolean isIncludeChildren() { return includeChildren; }
    public boolean isIncludeSelf() { return includeSelf; }
}
