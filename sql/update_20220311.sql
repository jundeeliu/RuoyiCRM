ALTER TABLE `master_tenant`
    CHANGE COLUMN `ID` `id` bigint(20) NOT NULL AUTO_INCREMENT FIRST,
    CHANGE COLUMN `TENANT` `tenant` varchar(32) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '租户ID' AFTER `id`,
    CHANGE COLUMN `URL` `url` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '数据库连接URL' AFTER `tenant`,
    CHANGE COLUMN `USERNAME` `username` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '用户名' AFTER `url`,
    CHANGE COLUMN `PASSWORD` `password` varchar(255) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '密码' AFTER `username`,
    CHANGE COLUMN `host` `host_name` varchar(64) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci NULL DEFAULT NULL COMMENT '数据库主机名' AFTER `database_name`,
    ADD COLUMN `status` char(1) default '1' COMMENT '状态(1正常 2停止)' AFTER `create_time`,
    ADD COLUMN `expiration_date` datetime NULL COMMENT '到期日期' AFTER `status`,
DROP PRIMARY KEY,
ADD PRIMARY KEY (`id`) USING BTREE,
DROP INDEX `idx_tenant`,
ADD UNIQUE INDEX `idx_tenant`(`tenant`) USING BTREE;
