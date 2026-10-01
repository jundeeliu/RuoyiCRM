-- Repeat in bounded batches until remaining_rows = 0. Stop on conflicts; reconcile manually.
SELECT COUNT(*) AS conflicting_rows FROM master_tenant
WHERE host IS NOT NULL AND host_name IS NOT NULL AND NOT (host <=> host_name);
UPDATE master_tenant SET host_name = host
WHERE host_name IS NULL AND host IS NOT NULL
ORDER BY id LIMIT 1000;
SELECT COUNT(*) AS remaining_rows FROM master_tenant
WHERE host_name IS NULL AND host IS NOT NULL;
