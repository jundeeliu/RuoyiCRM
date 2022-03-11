/*
 Navicat Premium Data Transfer

 Source Server         : localhost
 Source Server Type    : MySQL
 Source Server Version : 50732
 Source Host           : localhost:3306
 Source Schema         : rycrm-master

 Target Server Type    : MySQL
 Target Server Version : 50732
 File Encoding         : 65001

 Date: 14/02/2022 10:27:34
*/

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- ----------------------------
-- Table structure for master_tenant
-- ----------------------------
DROP TABLE IF EXISTS `master_tenant`;
CREATE TABLE `master_tenant` (
                                 `ID` bigint(20) NOT NULL AUTO_INCREMENT,
                                 `TENANT` varchar(32) DEFAULT NULL COMMENT '租户ID',
                                 `URL` varchar(255) DEFAULT NULL COMMENT '数据库连接URL',
                                 `USERNAME` varchar(255) DEFAULT NULL COMMENT '用户名',
                                 `PASSWORD` varchar(255) DEFAULT NULL COMMENT '密码',
                                 `database_name` varchar(64) DEFAULT NULL COMMENT '数据库名',
                                 `host` varchar(64) DEFAULT NULL COMMENT '数据库主机',
                                 `create_time` datetime DEFAULT NULL COMMENT '创建时间',
                                 PRIMARY KEY (`ID`),
                                 UNIQUE KEY `idx_tenant` (`TENANT`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=22 DEFAULT CHARSET=utf8mb4;

-- ----------------------------
-- Records of master_tenant
-- ----------------------------
BEGIN;
INSERT INTO `master_tenant` VALUES (1, 'tenant1', 'jdbc:mysql://localhost:3306/rycrm-tenant-1?useSSL=false', 'root', 'root', 'rycrm-tenant-1', 'localhost', NULL);
INSERT INTO `master_tenant` VALUES (2, 'tenant2', 'jdbc:mysql://localhost:3306/rycrm-tenant-2?useSSL=false', 'root', 'root', 'rycrm-tenant-2', 'localhost', NULL);
COMMIT;

-- ----------------------------
-- Table structure for sys_logininfor
-- ----------------------------
DROP TABLE IF EXISTS `sys_logininfor`;
CREATE TABLE `sys_logininfor` (
                                  `info_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '访问ID',
                                  `user_name` varchar(50) DEFAULT '' COMMENT '用户账号',
                                  `ipaddr` varchar(128) DEFAULT '' COMMENT '登录IP地址',
                                  `login_location` varchar(255) DEFAULT '' COMMENT '登录地点',
                                  `browser` varchar(50) DEFAULT '' COMMENT '浏览器类型',
                                  `os` varchar(50) DEFAULT '' COMMENT '操作系统',
                                  `status` char(1) DEFAULT '0' COMMENT '登录状态（0成功 1失败）',
                                  `msg` varchar(255) DEFAULT '' COMMENT '提示消息',
                                  `login_time` datetime DEFAULT NULL COMMENT '访问时间',
                                  PRIMARY KEY (`info_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=291 DEFAULT CHARSET=utf8mb4 COMMENT='系统访问记录';


-- ----------------------------
-- Table structure for sys_oper_log
-- ----------------------------
DROP TABLE IF EXISTS `sys_oper_log`;
CREATE TABLE `sys_oper_log` (
                                `oper_id` bigint(20) NOT NULL AUTO_INCREMENT COMMENT '日志主键',
                                `title` varchar(50) DEFAULT '' COMMENT '模块标题',
                                `business_type` int(2) DEFAULT '0' COMMENT '业务类型（0其它 1新增 2修改 3删除）',
                                `method` varchar(100) DEFAULT '' COMMENT '方法名称',
                                `request_method` varchar(10) DEFAULT '' COMMENT '请求方式',
                                `operator_type` int(1) DEFAULT '0' COMMENT '操作类别（0其它 1后台用户 2手机端用户）',
                                `oper_name` varchar(50) DEFAULT '' COMMENT '操作人员',
                                `dept_name` varchar(50) DEFAULT '' COMMENT '部门名称',
                                `oper_url` varchar(255) DEFAULT '' COMMENT '请求URL',
                                `oper_ip` varchar(128) DEFAULT '' COMMENT '主机地址',
                                `oper_location` varchar(255) DEFAULT '' COMMENT '操作地点',
                                `oper_param` varchar(2000) DEFAULT '' COMMENT '请求参数',
                                `json_result` varchar(2000) DEFAULT '' COMMENT '返回参数',
                                `status` int(1) DEFAULT '0' COMMENT '操作状态（0正常 1异常）',
                                `error_msg` varchar(2000) DEFAULT '' COMMENT '错误消息',
                                `oper_time` datetime DEFAULT NULL COMMENT '操作时间',
                                PRIMARY KEY (`oper_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=346 DEFAULT CHARSET=utf8mb4 COMMENT='操作日志记录';


SET FOREIGN_KEY_CHECKS = 1;
