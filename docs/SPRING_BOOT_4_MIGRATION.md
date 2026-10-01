# RuoyiCRM Spring Boot 2.5.8 → 4.1.1 migration contract

Source identity: `jundeeliu/RuoyiCRM@d742330901b40126f482c5f092ca1ba43a3c7ebc`. Target profile: Java 21, Spring Boot 4.1.1, Spring Security 7, MyBatis Spring Boot 4.1.0, PageHelper 4.1.1, Druid Boot 4 starter 1.2.28, springdoc 3.1.0, MySQL 8.4.11 and Redis 7.4.11 for the disposable local run. The source build needs JDK 11 and a recorded minimal POM fix for two dependencies whose modules are absent from upstream; see `docs/crit10/baseline-build-fix.patch`. This patch changes no baseline Java, route, mapper or business logic.

## Framework Contract Model (FCM)

| Surface | Source behavior/evidence | Target invariant and current evidence |
| --- | --- | --- |
| HTTP routes | 141 Controller route variants bound to file, line and SHA in `docs/crit04/ruoyicrm-150.json` | Route inventory preserved in source; real dual replay covers only cases with fixtures. |
| Authentication | Authorization bearer token, Redis backed `LoginUser`, source JWT HS512 secret in checked-in YAML | Required 64-byte Base64 key via `RUOYI_JWT_SECRET_BASE64`; old JWTs and Redis sessions require re-login. SecurityFilterChain and negative tests cover missing/forged token, cookie-only access denial and tenant mismatch. The Vue app currently keeps the token in a JS-readable cookie but sends it in the Authorization header; the server does not authenticate that cookie. |
| Error contract | Source unauthorized request returns HTTP 200 with AjaxResult `code=401` | Target returns HTTP 401 with the same AjaxResult `code=401`; this is an intentional breaking HTTP contract. Vue Axios error interceptor handles HTTP 401. Exact drift remains visible in Golden Master receipts. |
| JSON wire format | Source Spring Boot 2 MVC uses Jackson 2 annotations and the JVM time zone | Target explicitly prefers the Jackson 2 HTTP converter during migration. The initial Jackson 3 default changed property order and shifted synthetic `createTime` by eight hours; after the compatibility setting, 57 authenticated GETs match source response bytes exactly. Jackson 2 is a temporary Boot 4 compatibility path and needs a separate Jackson 3 migration before its removal. |
| Tenant routing | Request `tenant` header selects database; reused async threads can carry state | Unknown, absent and stale tenant keys fail closed; transaction-bound routing cannot switch databases; isolation and rollback tested on disposable MySQL. |
| Data scope | Five Mapper locations splice `${params.dataScope}` SQL text | Server-owned immutable criteria bind values with `#{}`; unannotated calls and invalid roles deny. Five BoundSql/forgery negative tests cover the rewrite. |
| Redis wire format | Fastjson 1.x AutoType global parser with class names | Explicit versioned JSON envelope accepts only known application cache types; legacy cache values fail closed. Map cycles, deep nesting and excessive entries are rejected. Cache namespace must be drained/rotated during rollout. |
| Persistence | 19 MyBatis Mapper XML, no JPA Entity/Query API | Mapper XML remains because it is SQL mapping, not Spring Bean XML. A physical MySQL route/transaction test runs; full 150 statement execution has not been shown. |
| Configuration | `spring.redis`, hard-coded DB/JWT material, Springfox Swagger | `spring.data.redis`, environment-only DB and JWT secrets, springdoc disabled by default, Druid console disabled. Configuration map is in `docs/crit04/API_CONFIG_CHANGELOG.md`. |
| Health | No proven source Actuator route | Target exposes health, liveness and readiness with redacted details; all other Actuator routes require authentication or are not exposed. Physical probes bind the exact target JAR. |
| Frontend | Vue 2 CLI client originally has no committed lockfile; Node 24 build hits MD4 compression failure | Locked Node 24/npm 11 install and native gzip build pass for production and staging, with 98 compressed assets checked each time. Axios and js-cookie high advisories are fixed. Lint still reports 4,533 errors and 1,382 warnings; production audit reports 4 moderate and 4 low advisories. Vue 2 remains unsupported. |
| Deployment | No checked-in Istio/Prometheus production topology | Expand/contract, canary and rollback are candidate artifacts under `deploy/cutover/`, with local tests only. |

## Reproducible local gates

```bash
JAVA_HOME=/path/to/jdk-21 mvn -B -ntp clean package
python3 scripts/check_java_parameter_metadata.py
python3 -m unittest discover -s tests -p 'test_*.py' -v
JAVA_HOME=/path/to/jdk-21 bash scripts/ci_spring4_sbom.sh
python3 scripts/crit_static_scan.py --bom target/bom.json
bash scripts/ci_spring4_frontend.sh build
bash scripts/ci_spring4_frontend.sh lint
bash scripts/ci_spring4_frontend.sh audit
bash scripts/ci_spring4_frontend.sh sbom
```

The `.buildkite/pipeline.yml` defines seven separately visible steps: frontend build, frontend lint, frontend production dependency audit, frontend CycloneDX SBOM, backend clean package and contracts, disposable MySQL/Redis routing, and aggregate Maven CycloneDX SBOM. Lint and audit currently fail and are not suppressed. A Buildkite organization must connect this repository and provide agents with JDK 21, Node 24/npm 11, Python 3, Maven and Docker before the hosted pipeline can execute. A valid local pipeline dry run is not a hosted CI result.

The local `docs/sbom/ruoyicrm-spring4.cdx.json` lists 154 resolved Maven components; `docs/sbom/ruoyicrm-ui.cdx.json` lists 1,336 lockfile-derived npm components. `docs/LOCAL_CRIT_STATIC.json` binds the Maven SBOM digest to 247 main Java files, 21 XML files and 7 POMs. Zero static findings cover the named patterns only. The isolated source and target stacks replayed 57 byte-identical authenticated GETs; 9 negative cases expose an intentional HTTP 200→401 contract change, and 84 cases remain `NOT_RUN` in the strict HTTP dual replay. A separate bounded notice write attempted only the source side; the target was not written after a second fence failure, and both disposable stacks were destroyed. The target started with circular references disabled and passed health, liveness and readiness probes. Frontend lint/audit, external infrastructure and independent verification remain separate gates.

## Rollout and compatibility limits

Rotate the JWT secret and Redis cache namespace together; users must sign in again. Keep old and new versions on separate disposable databases and Redis stores during qualification. Do not send mirrored writes to production or claim an automatic seconds-level rollback before a real Istio/Prometheus drill. Treat the observed HTTP 200→401 change as an API breaking change requiring client compatibility verification. `docs/crit04/PHYSICAL_REPLAY_EVIDENCE.md` records the exact local baseline/target result. E4/E5 and production certification remain `NOT_RUN` / `NOT_CERTIFIED`.
