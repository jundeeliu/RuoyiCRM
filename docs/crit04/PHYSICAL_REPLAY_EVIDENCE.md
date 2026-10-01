# RuoyiCRM CRIT-02/04 本地物理双栈回执（2026-10-02）

## 运行身份与边界

- 源版：Git `d742330901b40126f482c5f092ca1ba43a3c7ebc`，JDK 11 构建的 `ruoyi-admin.jar` SHA-256 `27e857f89ed7261f01242b58cf56713234dd6e138ab838f4c2a6ff3a07d506af`，本地 HTTP `127.0.0.1:53112`。原提交引用不存在的 `ruoyi-quartz` 和 `ruoyi-generator` 模块；隔离源码副本仅应用 `docs/crit10/baseline-build-fix.patch` 删除这两项 POM 依赖，未改 Java 业务源码。
- 目标版：JDK 21 / Spring Boot 4.1.1 的 `ruoyi-admin.jar` SHA-256 `6829de6eaaab1d60620235c7f7aef4430bd4bf19feacbd08872b12c2f336c161`，本地 HTTP `127.0.0.1:54610`，`SPRING_MAIN_ALLOW_CIRCULAR_REFERENCES=false`；日志出现 `Started RuoYiApplication`。根 POM 开启 Java `-parameters` 后，目标详细查询路由可绑定形参。此摘要绑定本次回放，不能由当前工作树状态反推。
- 两端分别使用 `deploy/crit10/compose.yaml` 启动的一次性 MySQL 8.4 / Redis 7 项目 `ruoyicrm-crit10-1580f1739c` 与 `ruoyicrm-crit10-4033f54722`，仅绑定 `127.0.0.1`。初始化只使用仓库 DDL 和两条合成租户路由数据，不导入源码样例账号或业务数据。启动时两端 `probe-receipt.json` 均为 `LOCAL_PHYSICAL_STACK_READY`，含 TCP、SQL 和 Redis PONG 检查；该初始探针早于后续合成鉴权 fixture。
- 两端 tenant1 库各有最小合成部门、角色、用户及关联各 1 行；随机一次性口令通过真实验证码及 `/login` 获得令牌。合成用户 `loginDate` 在登录前后固定为 `2020-01-01 00:00:00`，仅为固定响应 oracle。登录原代码写入 `sys_logininfor`。另在双方私有 uploads 目录放置相同合成文本文件，用于只读资源下载。口令、令牌、验证码和日志只保存在本地临时目录，不入库提交。GET 阶段结束时的非空表范围见 `expanded-post-replay-data-scope.json`：两端主库仅 `master_tenant` 2 行，tenant1 中上述四表各 1 行及 `sys_logininfor` 3 行，tenant2 空。行级差分和写后补偿仍 `NOT_RUN`。

## 66 条基线 oracle 的目标回放

`docs/crit04/baseline-oracles/` 包含 9 条未认证权限负向 oracle 和 57 条认证只读 GET oracle，均由固定源版真实 HTTP 采集，记录源提交、Controller 源码摘要和响应摘要。运行脚本从私有目录注入两端令牌：

```bash
CRIT04_BASELINE_TOKEN="$BASELINE_DISPOSABLE_TOKEN" CRIT04_TARGET_TOKEN="$TARGET_DISPOSABLE_TOKEN" \
python3 scripts/crit04_replay.py replay \
  --baseline http://127.0.0.1:53112 --target http://127.0.0.1:54610 \
  --fixtures docs/crit04/expanded-local-fixtures.json \
  --output docs/crit04/dual-replay-receipt.json
```

回执为 `planned=150, passed=57, failed=9, not_run=84`；脚本按严格失败语义退出码 `2`。57 条认证 GET 在 HTTP 状态、Content-Type、Content-Disposition、download-filename 和原始响应字节上完全一致。目标 Jackson 2 HTTP 转换器保留旧版序列化契约；`-parameters` 修复了目标详情查询的 10 条形参绑定失败。未对业务数据或随机字段作宽松归一化，规范化 JSON 摘要仅用于定位。

9 条 `RUOYICRM-142` 至 `150` 仍是 `BEHAVIOR_DRIFT`：源版 HTTP 200 / JSON `code:401`，目标 HTTP 401 / JSON `code:401`；响应体 SHA-256 一致，Content-Type 的 `charset=utf-8` 与 `charset=UTF-8` 大小写也不同。该 HTTP 401 是可观察的安全 API 变更，比较器没有豁免；`ruoyi-ui/src/utils/request.js` 已适配 Axios 的 HTTP 401 错误分支。84 条 `NOT_RUN` 包括 80 条非 GET 和 4 条逐项列于 `get-expansion-blockers.json` 的 GET：随机图片/Redis 写入、时间戳下载头、源版缺失 `sys_config` 表的详情查询，以及实际更新客户的 GET。不能将 150 条清单称为 150 条通过。

单独的 `RUOYICRM-059` 合成公告写入尝试见 `notice-write-receipt.json`：源端成功插入一行，第二次围栏失败后目标端未发送 POST。该用例在双栈回放统计中仍属 `NOT_RUN`，在写入回执中为 `FAIL` 部分执行；两套一次性 JVM、容器、卷和私有运行目录已销毁。没有证明自动补偿或快照恢复。

## Actuator 与 CRIT-02 启动探针

当前回放 JAR `6829de6eaaab1d60620235c7f7aef4430bd4bf19feacbd08872b12c2f336c161` 的本地无令牌探针观察到 `/actuator/health`、`/actuator/health/liveness`、`/actuator/health/readiness` 返回 HTTP 200 / `UP`，`/actuator/info` 和 `/actuator/prometheus` 返回 HTTP 401。进程、JAR 摘要、时间与逐路径状态记录在 `docs/crit10/current-jar-actuator-probe.json`。监控采集如果依赖 Prometheus 端点，仍需要经授权的独立采集方案。

静态 SCC 审计见 `docs/crit02/scc-audit.json`：193 个具体类、66 条解析注入边、33 条未解析边，Tarjan 在已解析子图中发现 0 个 SCC。当前目标在显式禁止 Spring 循环依赖时完成物理启动，仅证明当前装配路径。以上为 `LOCAL_EXECUTED_SELF_ATTESTED`；独立/外部验证 `NOT_RUN`，生产认证 `NOT_CERTIFIED`。
