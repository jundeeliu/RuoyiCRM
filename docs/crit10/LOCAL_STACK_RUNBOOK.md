# CRIT-10 隔离物理栈操作手册

此栈仅供 RuoyiCRM Spring 升级的本地 CRIT-10 前置验证。Compose 项目名、MySQL/Redis 回环端口和一次性强口令每次生成；数据保存在该项目专用卷。容器不会监听非 `127.0.0.1` 地址。

## SQL 输入边界

初始化器读取仓库 `sql/database.sql`、`rycrm-master.sql`、`rycrm-tenant.sql`、`quartz.sql` 和 `update_20220311.sql`，逐条解析并仅生成三库、3 张 master 表、每个 tenant 22 张业务表与 11 张 Quartz 表，以及 `master_tenant` 的版本变更。原始 dump 中的 `DROP TABLE`、356 条示例 `INSERT`、手机号、默认用户密码哈希及固定 `root` 租户连接不会被导入。只生成两条新的合成租户连接记录，引用该次栈的一次性端口与口令。

解析器发现未知 SQL 语句、库名漂移、重复表或迁移脚本漂移时会在容器启动前失败。运行时 SQL 错误会使 MySQL 初始化或表数量探针失败；不得加 `--force` 跳过错误。SQL 来源摘要与生成的初始化脚本摘要保存在私有 `state.json` 中。

## 启动与验证

```bash
python3 -m unittest discover -s tests -p 'test_crit10_stack.py' -v
python3 scripts/crit10_stack.py prepare
python3 scripts/crit10_stack.py up --state /path/printed/by/prepare/state.json
python3 scripts/crit10_stack.py probe --state /path/printed/by/prepare/state.json
```

`prepare` 打印的状态文件位于用户临时目录，权限为当前用户私有。`up` 如需拉取 `mysql:8.4` 会占用网络与磁盘。探针要求 MySQL 8.4、Redis 7、两个 TCP 端口、实际 Docker `127.0.0.1` 绑定、三库正确表数、两条合成租户记录及 Redis 认证 `PONG`。有界回执存放在同一临时目录的 `probe-receipt.json`，不含口令。

如果需基线与目标双轨运行，分别执行两次 `prepare`/`up`，获得两个不同 Compose 项目、MySQL/Redis 卷和回环端口。应用环境变量使用各自状态文件中的端口；口令只从私有 `mysql-app.cnf`、`redis-password` 文件读取并注入进程环境。两个应用不得共享数据库或 Redis。原始 SQL 用户记录未导入，因此登录与 150 场景回放仍需额外创建脱敏、可销毁的测试用户和 fixture。

## 关闭与销毁

```bash
python3 scripts/crit10_stack.py down --state /path/printed/by/prepare/state.json
```

`down` 只针对状态文件内的 `ruoyicrm-crit10-*` 项目执行 `docker compose down --volumes`，随后删除本次私有口令和生成 SQL。先保留不含口令的探针回执到任务证据目录，再销毁运行目录。不得对其他 Docker 项目执行清理。

本地栈可用仅表示 `LOCAL_PHYSICAL_STACK_READY`；Spring 应用启动、真实业务回放、独立 E4 与生产认证仍需各自证据，不能由此回执代替。
