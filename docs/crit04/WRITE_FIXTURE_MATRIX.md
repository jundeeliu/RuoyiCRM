# Non-GET fixture matrix for disposable RuoyiCRM replay

[`write-fixture-matrix.json`](write-fixture-matrix.json) binds all **80** non-GET cases in the source-bound 150-case manifest to an exact controller path, line, SHA-256, Java signature, request shape, synthetic prerequisites, side-effect targets, and planning status. Every case remains `NOT_RUN`; no expected status or baseline body hash was invented.

| Class | Cases | Current gate |
| --- | ---: | --- |
| Direct synthetic row candidate | 11 | Nine concrete bodies prepared; parent ID and private password unresolved in two; all lack snapshots, auth proof, and baseline oracle |
| Synthetic workflow or existing-row dependency | 50 | Create/seed referenced rows, verify tenant/role/owner state, snapshot before/after |
| Binary export/template oracle | 13 | Capture and compare binary response and audit side effects; JSON comparator is inapplicable |
| File upload/import/avatar | 3 | Private temporary storage, bounded files, cleanup and file-system reconciliation |
| Credential rotation | 2 | Disposable accounts, known old password, re-login and restore plan |
| Tenant database creation | 1 | Dedicated disposable MySQL administrator scope and database cleanup plan |

The 80 rows are **fixture specifications**, not executable fixtures. `tests/test_crit04_write_matrix.py` checks exact manifest coverage and source digests, request-body and path-parameter shape, and a future fixture's required fields/oracle. It does not send requests. A future fixture must declare `environment=TWO_DISPOSABLE_STACKS_ONLY`, the tenant/token binding where applicable, the named JSON/form/multipart/path fields, and baseline `expected_status` plus `expected_body_sha256`. Per-case values must be created from synthetic rows on two separate disposable stacks, then captured by the approved baseline workflow.

Special paths require more than a generic HTTP replay. `/login` depends on fresh CAPTCHA state and writes a Redis session; the source manifest labels it `AUTHENTICATED`, but the controller itself does not consume an existing token. `/register` is excluded from the tenant interceptor and creates a new database, so it is blocked pending a dedicated workflow. Profile password and user reset endpoints change credentials. Role grants and data scope need a synthetic user/role/department graph. CRM transfers, clue conversion, pool moves, and order approval need ordered state transitions and database reconciliation. Audit log clean endpoints can erase all rows in their tables; only disposable synthetic data may be used.

The existing `scripts/crit04_replay.py` still blocks non-GET requests unless `--allow-writes` is passed. Do not use that flag based solely on this matrix. Immediately before each permitted write, integrate `scripts.dualrun.fence.authorize_write` and verify both application-to-stack bindings and tenant JDBC URLs. The fence is a local, time-bound preflight; it does not provide distributed transaction compensation. If one side succeeds and the other fails, quarantine the case and restore both disposable stacks from pre-case snapshots. Never infer PASS from a fixture plan or a self-attested local receipt.
