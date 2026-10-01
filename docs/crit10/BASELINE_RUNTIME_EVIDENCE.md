# RuoyiCRM d7423309 本地物理基线记录

记录日期：2026-10-02（Asia/Shanghai）。证据级别：`LOCAL_EXECUTED_SELF_ATTESTED`；外部验证 `NOT_RUN`，生产认证 `NOT_CERTIFIED`。

- 基线源码为独立 detached 工作树 `/tmp/ruoyicrm-crit10-baseline-d7423309`，HEAD 为 `d742330901b40126f482c5f092ca1ba43a3c7ebc`。
- 原提交在 JDK 21 编译时触发旧 Lombok 与 javac `JCImport.qualid` 不兼容。切到本机 JDK 11 后，Maven 又发现 `ruoyi-admin/pom.xml` 引用仓库中不存在的 `ruoyi-quartz`、`ruoyi-generator` 两个模块。仅在临时基线工作树按 [baseline-build-fix.patch](baseline-build-fix.patch) 删除这两个依赖块；仓库 Java 源码、Controller、Mapper、配置及业务逻辑未修改。`mvn -q -pl ruoyi-admin -am -DskipTests package` 随后通过。
- 基线应用以 JDK 11 从构建出的 `ruoyi-admin.jar` 启动，并出现 `Started RuoYiApplication`。独立的 CRIT-10 项目提供 MySQL 8.4.11、Redis 7.4.11；数据库分别为 `rycrm-master`、`rycrm-tenant-1`、`rycrm-tenant-2`。其回环端口、一次性口令和私有启动日志保存在本机临时状态目录，不写入仓库。
- 真实基线的 9 条未认证权限用例 `RUOYICRM-142` 至 `150` 已采集到 `docs/crit04/baseline-oracles/`；每条返回 HTTP 200、业务 `code:401`。之后在仅含合成账号、部门、角色及关联的 tenant1 库上经真实验证码和 `/login` 获得一次性令牌，共采集 57 条认证只读 GET oracle。合成用户的登录时间被固定为确定值，资源下载使用私有合成文本文件；这些仅界定本次 fixture，不代表真实用户行为。当前目标双栈的严格回放为 57 `PASS`、9 `FAIL`、84 `NOT_RUN`，运行身份、差异和写入范围见 `docs/crit04/PHYSICAL_REPLAY_EVIDENCE.md`。剩余 84 条没有完整可执行 oracle 或安全写入前提。

基线启动不证明目标启动、业务等价、数据库写后状态、独立 E4 或生产可用。原始基线 `TenantInterceptor` 可能在日志中打印租户对象，因此私有日志不得上传或原样展示；目标分支应移除该日志后再做有租户请求的回放。
