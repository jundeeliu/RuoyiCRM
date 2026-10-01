# RuoyiCRM API 与配置迁移清单（2026-10-02）

基线提交：`d7423309`。本清单绑定当前工作树中的真实 Controller 与 Mapper 源码；[ruoyicrm-150.json](ruoyicrm-150.json) 保存 150 个待回放用例。它们由 141 个 Controller 路由和 9 个未认证权限变体组成。19 个 Mapper XML 中另有 150 条带文件、行号的 SQL 声明。路由和 SQL 的数量来自 `python3 scripts/crit04_replay.py check`，不代表已经运行或验证行为等价。

## API 变更记录

Controller 路由和请求/响应模型未改。回放清单逐项记录 HTTP 方法、路径模板、Java 方法、`@PreAuthorize` 表达式、源码行和 SHA-256；例如 `/login`、`/crm/customer/list`、`/system/user/list`。动态路径值、认证令牌和请求体由隔离环境的 fixture 注入。没有 fixture 的用例保持 `NOT_RUN`。

当前 JAR 的本地物理双栈已执行 66/150 条：57 条合成账号的认证只读 GET 在 HTTP 状态、下载相关响应头和响应体字节上完全一致；9 条未认证权限 GET 是明确的安全契约变更，源版 HTTP 200 / JSON `code:401`，目标 HTTP 401 / 相同 JSON `code:401` 和相同响应体字节，严格比较器仍记 `FAIL`。`ruoyi-ui/src/utils/request.js` 已适配 Axios 的 HTTP 401 错误分支。另有 84 条保持 `NOT_RUN`：80 条非 GET 未执行安全写入回放，4 条 GET 有逐项阻断记录 `get-expansion-blockers.json`。不能把 150 条清单计作 Golden Master 全通过，独立验证也未完成。

目标版显式启用 Jackson 2 HTTP 消息转换兼容选项后，之前观察到的 JSON 属性顺序和 8 小时时间字段漂移消失。目标 Maven 编译器增加 `-parameters` 后，多个路径参数 GET 的 Spring MVC 500 装配错误消失。当前运行身份、逐项结果与受限数据库写入范围见 `PHYSICAL_REPLAY_EVIDENCE.md`、`dual-replay-receipt.json` 和 `expanded-post-replay-data-scope.json`。

## 配置映射与验收义务

| 当前配置位置 | 当前键或环境输入 | 目标验收义务 | 状态 |
| --- | --- | --- | --- |
| `ruoyi-admin/src/main/resources/application.yml` | `server.port` / `RUOYI_HTTP_PORT` | 基线与目标使用不同的回环端口；验证 context path、错误码与响应头 | 局部执行：66 条 GET |
| 同上 | `spring.data.redis.*` / `RUOYI_REDIS_*` | 两个运行栈接入不同的隔离 Redis 实例或库；验证会话、验证码和退出登录 | 验证码与登录局部执行；退出登录 NOT_RUN |
| 同上 | `token.header`, `token.secret`, `token.expireTime` / `RUOYI_JWT_SECRET_BASE64` | 验证 JWT 签发、过期、拒绝路径和权限语义；密钥由隔离环境注入 | 签发、认证 GET、未认证拒绝局部执行；过期 NOT_RUN |
| 同上 | `spring.http.converters.preferred-json-mapper` | 保留源版 Jackson 2 响应序列化；检查时间字段及属性顺序 | 57 条认证 GET 字节一致 |
| 同上 | `mybatis.mapperLocations`, `mybatis.configLocation` | 验证 19 个 Mapper XML 全部加载，150 条 SQL 声明可解析并在目标数据库执行 | NOT_RUN |
| 同上 | `springdoc.*`, `swagger.*` | 验证 API 文档暴露开关和认证边界 | NOT_RUN |
| `ruoyi-admin/src/main/resources/application-druid.yml` | `spring.datasource.druid.master.*` / `RUOYI_MASTER_*` | 基线与目标分别接入一次性 MySQL 数据库；比较写前/写后表级与行级状态 | 一次性栈启动及非空表范围已检查；行级差分 NOT_RUN |
| 同上 | `spring.datasource.druid.slave.*` | 禁用时验证主库回退；启用时验证只读路由和事务边界 | NOT_RUN |
| 同上 | `tenant.database.*` / `RUOYI_TENANT_DB_*` | 使用一次性租户库；验证租户隔离和建库权限 | tenant1 合成登录/GET 和 tenant2 零行已检查；建库权限 NOT_RUN |

配置键的目标版本兼容性和默认值必须通过真实目标启动日志、绑定检查和回放验证。静态文件存在不算 Spring Boot 4 运行证据。

## 循环依赖审计

`python3 scripts/crit02_scc_audit.py --output docs/crit02/scc-audit.json` 对当前源码中的 `@Autowired`、`@Resource` 字段和显式 `@Autowired` 构造函数建立有源位置的依赖图。当前审计解析了 193 个具体类、66 条注入边，Tarjan 在已解析子图中未发现 SCC；33 条外部框架或 Mapper 注入边保留为未解析清单。目标 JAR 已在 `SPRING_MAIN_ALLOW_CIRCULAR_REFERENCES=false` 下完成物理启动；静态报告中 `runtime_startup: NOT_RUN` 仅说明扫描器自身不作运行时证明。没有可证明的源码环，因此未制造事件或 SPI 补丁。
