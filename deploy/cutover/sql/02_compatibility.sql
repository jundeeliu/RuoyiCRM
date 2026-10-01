-- Apply after 01_expand; reject conflicting dual writes instead of silently losing one side.
-- Requires no pre-existing master_tenant INSERT/UPDATE triggers (00_preflight).
DELIMITER //
CREATE TRIGGER cutover_master_tenant_bi BEFORE INSERT ON master_tenant FOR EACH ROW
BEGIN
  IF NEW.host IS NOT NULL AND NEW.host_name IS NOT NULL AND NOT (NEW.host <=> NEW.host_name) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'host and host_name conflict';
  END IF;
  SET NEW.host = COALESCE(NEW.host, NEW.host_name);
  SET NEW.host_name = COALESCE(NEW.host_name, NEW.host);
END//
CREATE TRIGGER cutover_master_tenant_bu BEFORE UPDATE ON master_tenant FOR EACH ROW
BEGIN
  IF NOT (NEW.host <=> OLD.host) AND NOT (NEW.host_name <=> OLD.host_name)
     AND NOT (NEW.host <=> NEW.host_name) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'concurrent host fields conflict';
  END IF;
  IF NOT (NEW.host <=> OLD.host) THEN
    SET NEW.host_name = NEW.host;
  ELSEIF NOT (NEW.host_name <=> OLD.host_name) THEN
    SET NEW.host = NEW.host_name;
  ELSEIF NOT (NEW.host <=> NEW.host_name) THEN
    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'pre-existing host fields conflict';
  END IF;
END//
DELIMITER ;
