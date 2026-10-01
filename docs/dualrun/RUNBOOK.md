# RuoyiCRM dual-run differential and write fence

The library in `scripts/dualrun/` is a local component for CRIT-04 replay. It does not send HTTP requests or execute writes. `compare.compare_http(left, right, rules)` accepts two captured responses with exact `status`, `content_type`, and UTF-8 JSON `body` bytes. It compares status, Content-Type, JSON keys, array order, value types, and all deterministic values. Rules are **per case** exact JSON Pointers: `[{"path":"/uuid","kind":"uuid"}]`. The only supported kinds are `timestamp`, `uuid`, `token`, and `trace_id`; wildcard, root, duplicate, overlapping, missing, malformed, and wrong-type fields fail closed. A rule applies only to its named field and must be reviewed against the source controller.

Source-bound examples:

- `/captchaImage` in `CaptchaController` returns `/uuid` from `IdUtils.simpleUUID()`. An exact `/uuid` UUID rule can normalize that field. `/img` is nondeterministic CAPTCHA image data and is **not** in the generic allowlist; its mismatch remains visible until a separately justified image contract is defined.
- `/login` in `SysLoginController` returns `/token` from `TokenService`. The `token` rule requires a JWT with `HS512`, a 64-byte signature, a nonempty `tenant` claim and a UUID `login_user_key`; it masks only the random user key and signature while preserving the tenant and every other claim for comparison. It does not cryptographically verify the signature; authentication tests must verify token usability separately.
- Timestamp rules accept only timezone-bearing ISO 8601 strings. A business timestamp such as an order's committed time must not be allowlisted simply because it differs. Trace IDs must be 16 or 32 hex characters.

For offline CLI use, write each response as a private JSON file with exact keys `status`, `content_type`, `body_base64`. Store the rules as a JSON list and run `python3 -m scripts.dualrun.cli compare --left LEFT.json --right RIGHT.json --rules CASE_RULES.json`. Exit 0 means equality, 1 means observed drift, 2 means invalid input or rules. Neither bodies nor token values are printed by the CLI. The existing `scripts/crit04_replay.py` currently records body SHA only; integration requires preserving bounded raw response bytes in a private local artifact or passing them directly to `compare_http`. A SHA alone cannot support field-level canonicalization.

## Write isolation fence

Before **each** non-GET replay request, an orchestrator may call `fence.authorize_write(...)` or `python3 -m scripts.dualrun.cli fence-write ...`. The fence is read-only. It requires two private CRIT-10 `state.json` and fresh `probe-receipt.json` files, successful initial synthetic-data checks, and live Docker Compose inspection proving distinct project names, loopback MySQL/Redis ports, container IDs, image IDs, and named data volumes. It also reads the two synthetic `master_tenant` rows from each disposable master database to verify that tenant JDBC URLs point to that stack's own MySQL port. It then requires a private `source-app.json` / `target-app.json` in the matching runtime directory, a live Java `-jar` PID with the recorded artifact SHA, exact `RUOYI_*` MySQL/Redis/HTTP environment port bindings, current TCP sockets to both dedicated storage ports, and the exact loopback HTTP URL for each PID. Missing or stale evidence blocks writes. The process environment is inspected in memory; raw environment strings and credential values must never be logged or retained.

The fence additionally requires a **separate, recent pre-case snapshot for each stack**. Each private runtime must contain `prewrite-snapshot.json` bound to its project, live container IDs, volume names, method and path, plus `prewrite-mysql.sql` and `prewrite-redis.rdb` with matching byte sizes and SHA-256 digests. The verifier checks MySQL dump and Redis RDB format prefixes, not full restore correctness. `snapshot.py` captures those artifacts with `mysqldump --single-transaction` and `redis-cli --rdb`, using private local credentials and files. It invalidates the previous receipt before capture. No restore test or cross-store atomicity is claimed: MySQL and Redis are snapshotted sequentially. A fabricated receipt or an untested backup is not sufficient for a production recovery claim.

For the direct synthetic notice candidate, **after explicit handoff of two fresh, separate, disposable stacks**, run from the repository root with private path variables substituted from that handoff. This sequence captures no business writes:

```sh
python3 -m scripts.dualrun.snapshot capture --state "$SOURCE_STATE" --method POST --path /system/notice
python3 -m scripts.dualrun.snapshot capture --state "$TARGET_STATE" --method POST --path /system/notice
python3 -m scripts.dualrun.cli fence-write \
  --source-state "$SOURCE_STATE" --target-state "$TARGET_STATE" \
  --source-app "$SOURCE_APP" --target-app "$TARGET_APP" \
  --source-snapshot "$(dirname "$SOURCE_STATE")/prewrite-snapshot.json" \
  --target-snapshot "$(dirname "$TARGET_STATE")/prewrite-snapshot.json" \
  --source-url "$SOURCE_URL" --target-url "$TARGET_URL" \
  --method POST --path /system/notice
```

Require exit 0 and `LOCAL_WRITE_FENCE_PASSED` immediately before each request. A new case needs a new snapshot pair bound to its method/path. Record private pre-case MySQL rows and Redis keys for the exact synthetic business identifier, then compare both HTTP responses and post-case rows. If any step fails, retain `NOT_RUN` or `FAIL`; discard the disposable stacks or test restore in another disposable environment. Never print snapshot contents, credential files, raw tokens, or `ps eww` output.

The bounded `RUOYICRM-059` runner is `python3 -m scripts.dualrun.replay_notice` with the same ten fence arguments above, plus `--fixture docs/crit04/direct-write-fixtures-candidates.json --receipt docs/crit04/notice-write-receipt.json`. It reads `CRIT04_BASELINE_TOKEN` and `CRIT04_TARGET_TOKEN` from the caller's private process environment and never prints them. It refuses pre-existing synthetic notice rows, verifies each fence again immediately before its POST, and reads all ten `sys_notice` columns plus table counts in tenant1 and tenant2 on both stacks. The auto-generated positive `notice_id` and valid SQL `create_time` are type-checked then explicitly normalized; the other eight columns are compared exactly. MySQL version, server charset, timezone and table engine are recorded and must match. This is a one-case local check, not Batch 31 detail-level independent reconciliation. Once an HTTP write is attempted, a later gate, transport, or query failure is recorded as `FAIL` with an indeterminate partial outcome; discard both stacks after preserving evidence. The runner performs no second candidate.

The observed first run is [notice-write-receipt.json](../crit04/notice-write-receipt.json): the source POST succeeded and inserted one synthetic `sys_notice` row, but the second preflight raised `FenceError` before the target POST. The initial runner retained only the exception type, so the exact failed assertion is unknown. Subsequent read-only fence checks passed but cannot establish the earlier cause. The case remains `FAIL` with target `NOT_RUN`; both dedicated JVMs and Compose projects/volumes were destroyed after poststate and snapshot hashes were recorded. The runner now records the fixed `FenceError` assertion text on future failures without logging process environments or credentials.

This is a **local preflight**, not a durable authorization token. Call it immediately before each write, use only disposable fixtures, and stop on any non-PASS result. The current CRIT-04 replay did not contain an independently verified app-to-stack binding receipt and its non-GET cases remain `WRITE_ISOLATION_NOT_AUTHORIZED`; the library does not retroactively authorize them. Do not use these assets with customer or production databases. The CLI only reports a bounded `LOCAL_WRITE_FENCE_PASSED` receipt; it never issues HTTP writes.

## Dual-write compensation boundary

Replay writes are two independent HTTP operations. If the first succeeds and the second fails, this package has no XA coordinator or domain-specific compensating action. Do **not** retry blindly: detect the partial outcome, quarantine the case, compare database/Redis state, and discard or restore both disposable stacks to their pre-case snapshot. Any compensation for a real business operation needs an explicit idempotency key, source/target transaction contract, tested inverse operation, and independent recovery evidence. No production write, automated compensation, or E4/E5 certification is claimed here.

Local tests: `python3 -m unittest tests.test_dualrun_compare tests.test_dualrun_fence tests.test_dualrun_snapshot -v`. They use synthetic HTTP bodies and mocked Docker/process inspection; they do not call the current physical stacks.
