-- Read-only contract gate. Both counts MUST be zero; also require release-owner evidence
-- that every legacy writer is drained and rollback no longer needs host.
SELECT COUNT(*) AS divergent_host_rows FROM master_tenant
WHERE NOT (host <=> host_name);
SELECT COUNT(*) AS invalid_status_rows FROM master_tenant
WHERE status NOT IN ('1', '2') OR status IS NULL;
SELECT COUNT(*) AS active_compatibility_triggers FROM information_schema.triggers
WHERE trigger_schema = DATABASE() AND event_object_table = 'master_tenant'
  AND trigger_name IN ('cutover_master_tenant_bi', 'cutover_master_tenant_bu');
