
<h1 align="center" style="margin: 30px 0 30px; font-weight: bold;">RuoyiCRM</h1>
<h4 align="center">基于若依Vue平台搭建</h4>


## 系统简介

RuoyiCRM基于若依平台二次开发的开源CRM系统，以SaaS方向实现多租户功能，动态创建数据库，独立数据库安全级别，不是按字段隔离。

* 多租户功能，物理数据库隔离。
* 前端采用Vue、Element UI。
* 后端采用Spring Boot、Spring Security、Redis & Jwt。
* 权限认证使用Jwt，支持多终端认证系统。
* 支持加载动态权限菜单，多方式轻松权限控制。

项目不断迭代中，欢迎Star，给我一些动力。谢谢！

 **演示项目已支持注册功能，自动生成数据库。欢迎提BUG交流~** [https://ruoyi.devjd.com/register](https://ruoyi.devjd.com/register)

## CRM系统功能
1.  公海管理：等待跟进的客户资源。
2.  线索管理：记录线索信息后续转成客户。
3.  客户管理：对客户信息进行管理及以跟进。
4.  订单管理：管理成交客户订单信息。

## Ruoyi-Vue内置功能

1.  用户管理：用户是系统操作者，该功能主要完成系统用户配置。
2.  部门管理：配置系统组织机构（公司、部门、小组），树结构展现支持数据权限。
3.  岗位管理：配置系统用户所属担任职务。
4.  菜单管理：配置系统菜单，操作权限，按钮权限标识等。
5.  角色管理：角色菜单权限分配、设置角色按机构进行数据范围权限划分。
6.  字典管理：对系统中经常使用的一些较为固定的数据进行维护。
7.  参数管理：对系统动态配置常用参数。
8.  通知公告：系统通知公告信息发布维护。
9.  操作日志：系统正常操作日志记录和查询；系统异常信息日志记录和查询。
10. 登录日志：系统登录日志记录查询包含登录异常。
11. 在线用户：当前系统中活跃用户状态监控。

**删除了系统工具及代码生成等模块。

## 在线体验
- tenant1/admin/admin123
- tenant2/admin/admin123

演示地址：https://ruoyi.devjd.com

管理后台演示地址：https://ruoyiboss.devjd.com (BOSS业务运营支撑系统)


## 数据库

1.  首先建立主数据库：rycrm-master，执行rycrm-master.sql脚本
2.  建立租户数据库（手动）：rycrm-tenant-1与rycrm-tenant-2
3.  rycrm-master的master_tenant表增加租户的数据库连接信息，rycrm-master.sql里内置了两条记录。

 **注：新版本中已经不需要手动创建tenant数据库了，注册的时候系统会自动创建。** 

## 项目导图

![输入图片说明](https://oscimg.oschina.net/oscnet/up-fc18a6102b182f0eb981e1114be155dbca4.png)

## 演示图

| ![输入图片说明](https://oscimg.oschina.net/oscnet/up-1c47cfe91d0efaad4286b9570e1a8659493.png) | ![输入图片说明](https://oscimg.oschina.net/oscnet/up-1c47cfe91d0efaad4286b9570e1a8659493.png) |
|---|---|
| ![输入图片说明](https://oscimg.oschina.net/oscnet/up-1eb62b24f1c041663f2218ce4038ff6588c.png) | ![输入图片说明](https://oscimg.oschina.net/oscnet/up-bbfcc53984cc7dd60bddaba796e6c36a0bd.png) |
| ![输入图片说明](https://oscimg.oschina.net/oscnet/up-ca9cee342c98170c08645e4177187f5e4e3.png) | ![输入图片说明](https://oscimg.oschina.net/oscnet/up-3198b72e4d47f55d3b447f003dd033c9bea.png) |

## 交流群 
QQ群： [![加入QQ群](https://img.shields.io/badge/556427333-blue.svg)](https://jq.qq.com/?_wv=1027&k=0vwIveTF) 点击按钮入群。
