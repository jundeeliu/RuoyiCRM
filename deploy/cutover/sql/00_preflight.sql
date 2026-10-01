-- Read-only gate. Run against a disposable clone first; database must be rycrm-master.
SELECT DATABASE() AS selected_database, VERSION() AS mysql_version;
SELECT column_name, column_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_schema = DATABASE() AND table_name = 'master_tenant'
ORDER BY ordinal_position;
SELECT trigger_name, event_manipulation, action_timing
FROM information_schema.triggers
WHERE trigger_schema = DATABASE() AND event_object_table = 'master_tenant';
SELECT COUNT(*) AS tenant_rows, COUNT(DISTINCT tenant) AS distinct_tenants,
       SUM(tenant IS NULL) AS null_tenants
FROM master_tenant;
