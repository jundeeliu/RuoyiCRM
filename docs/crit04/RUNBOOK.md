# CRIT-02 / CRIT-04 隔离运行与回滚手册

## 1. 前提

- 固定基线 `d7423309` 与待验目标提交；分别构建并启动在不同的回环端口。
- 为两端各准备独立、一次性的 MySQL 数据库及 Redis 实例/库，灌入同一脱敏种子快照。禁止指向生产服务。写请求必须在可重建的隔离数据上执行。
- 由环境注入 `RUOYI_*` 连接参数、`RUOYI_JWT_SECRET_BASE64` 和回放令牌。不得把密钥或真实用户资料写进 fixture、日志或收据。
- 基线和目标启动、MyBatis Mapper 加载、认证、数据库连接与 Redis 连接均需有独立日志。缺一项就记录 `NOT_RUN`。

## 2. 静态审计与清单防漂移

```bash
python3 scripts/crit02_scc_audit.py --output docs/crit02/scc-audit.json
python3 scripts/crit04_replay.py check
python3 -m unittest discover -s tests -p 'test_crit02_04_delivery.py' -v
```

`ZERO_STATIC_SCC` 仅覆盖审计脚本列出的解析边。若目标应用启动报循环引用，先定位实际 Bean 与注入边，在源码中通过低层 SPI 或事件解耦并验证事务、事件顺序，再重新运行扫描与启动；不得开启 `spring.main.allow-circular-references` 规避问题。

## 3. 生成 fixture 并回放

fixture JSON 以 `RUOYICRM-001` 等用例 ID 为键。每项可包含 `path_params`、`query` 和 `json`；写请求必须提供显式 `json`。例如：

```json
{
  "RUOYICRM-001": {"tenant": "tenant1", "expected_status": 200, "expected_body_sha256": "<baseline response SHA-256>"},
  "RUOYICRM-002": {"tenant": "tenant1", "expected_status": 200, "expected_body_sha256": "<baseline response SHA-256>", "path_params": {"id": "isolated-fixture-id"}, "query": {"pageNum": "1"}}
}
```

先运行无服务检查，确认 150 条全部 `NOT_RUN`：

```bash
python3 scripts/crit04_replay.py replay --output docs/crit04/replay-not-run.json
```

双栈启动并载入 fixture 后，在独立回环端口执行：

```bash
CRIT04_BASELINE_TOKEN="$BASELINE_TOKEN" CRIT04_TARGET_TOKEN="$TARGET_TOKEN" \
python3 scripts/crit04_replay.py replay \
  --baseline http://127.0.0.1:18080 --target http://127.0.0.1:28080 \
  --fixtures /path/to/disposable-fixtures.json \
  --output /path/to/replay-receipt.json
```

每条 fixture 必须给出从真实基线确认的 `expected_status`；AjaxResult 类结果还应给出 `expected_json_code`。需权限的认证变体必须同时提供两端令牌。写请求只有在两个环境均确认接入一次性数据源、已保存写前快照并准备回滚时，才增加 `--allow-writes`。此脚本比较 HTTP 状态、`Content-Type`、`Content-Disposition`、`download-filename`、JSON `code` 和响应体精确字节；规范化 JSON 摘要只辅助定位，不改变精确比较的失败判定。动态字段若导致差异必须显式审查规则和原始报文，不能泛化忽略。MySQL/Redis 写后状态、事务补偿、MockMvc 和权限语义需另附运行证据。即使 HTTP 150/150 通过，也仅是本地自检，不能自签 E4/E5。

基线 oracle 应先从固定提交的真实应用生成。下例仅捕获单条用例，不修改数据；输出包含基线提交、Controller 源码摘要、HTTP 状态、业务 `code` 与响应 SHA-256，不保存响应明文或令牌：

```bash
python3 scripts/crit04_replay.py capture \
  --baseline http://127.0.0.1:18080 \
  --baseline-source-root /path/to/d7423309-checkout \
  --case-id RUOYICRM-142 \
  --fixtures docs/crit04/unauth-fixtures.json \
  --output /path/to/RUOYICRM-142-baseline.json
```

回放 fixture 需复制该 oracle 的 `fixture_expectation`，至少包含 `expected_status` 与 `expected_body_sha256`。当前 `docs/crit04/baseline-oracles/` 中有 9 条未认证负向用例和 57 条认证只读 GET 的本地物理基线采集；其余 84 条没有完整 oracle/fixture 或安全写入前提，保持 `NOT_RUN`。4 条 GET 的逐项阻断见 `get-expansion-blockers.json`。源版未认证响应是 HTTP 200 加 JSON `code:401`，比较器同时检查这两个值；目标版 HTTP 401 是明确的 API 变更，严格比较保持 `FAIL`。

57 条认证只读 GET 使用 `scripts/crit04_seed_synthetic_auth.py` 在两套一次性 tenant1 库各建立一组最小合成部门、角色、用户和用户角色关系。脚本先确认这些表全空，使用一次性随机口令和 BCrypt，只把口令放到 CRIT-10 私有运行目录，不读取仓库的样例 INSERT。`scripts/crit04_synthetic_login.py` 向两套隔离 Redis 写入 180 秒验证码并经真实 `/login` 获取令牌；令牌仅保存于私有运行目录。对 `/getInfo`、`/system/user/profile`、`/system/user/{userId}`，脚本可用 `--freeze-login-date` 仅将合成用户的波动登录时间在两端固定为同一测试值，再次签发令牌；这一测试夹具不证明真实登录时间行为。`/common/download/resource` 使用两端私有上传目录中的同字节合成 `.txt` 文件；比较器同时核对下载头。`expanded-local-fixtures.json` 合并了 66 条无秘密期望。脚本支持的状态路径、HTTP URL 和输出路径必须分别指向两个独立回环栈；已有账号或状态文件时种子脚本拒绝覆盖。登录会在一次性 tenant1 库更新合成用户登录信息并写入 `sys_logininfor`，因此不应把认证引导过程称为纯只读。

## 4. 停止、恢复与交接

任一写请求落到非隔离库、认证行为扩大、出现数据差异或目标启动失败时，立即停止目标流量与回放；保存不含密钥的日志、请求摘要、数据库快照和目标提交。将灰度流量切回基线，销毁一次性数据库和 Redis，重建后才可重试。不能通过忽略失败场景、关闭 CSRF/权限或清空数据库差异来提高通过率。

当前交接状态（2026-10-02，本地隔离栈）：`CRIT-02` 静态解析子图零 SCC，目标 JAR 在 `SPRING_MAIN_ALLOW_CIRCULAR_REFERENCES=false` 下完成物理启动。`CRIT-04` 150 条已编目；57 条认证只读 GET 字节级 `PASS`，9 条未认证负向 GET 因源版 HTTP 200 与目标 HTTP 401 而判为 `BEHAVIOR_DRIFT`，尽管 JSON `code:401` 和响应体字节完全一致；另有 84 条 `NOT_RUN`（4 条 GET、80 条非 GET）。数据库非空表范围检查见 `expanded-post-replay-data-scope.json`；行级差分、写后补偿和独立验证 `NOT_RUN`，生产认证 `NOT_CERTIFIED`。详细运行身份见 `PHYSICAL_REPLAY_EVIDENCE.md`。
