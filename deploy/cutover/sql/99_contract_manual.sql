-- DESTRUCTIVE, MANUAL ONLY. Never run during canary or while rollback to legacy is possible.
-- Requires 90_contract_preflight zero divergence, legacy writers drained, backup/restore drill,
-- and an approved change record. DDL is not transactionally reversible in MySQL.
DROP TRIGGER cutover_master_tenant_bi;
DROP TRIGGER cutover_master_tenant_bu;
ALTER TABLE master_tenant DROP COLUMN host, ALGORITHM=INSTANT, LOCK=DEFAULT;
