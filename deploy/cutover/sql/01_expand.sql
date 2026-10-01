-- MySQL 8.4.11 clone-qualified candidate. Fails if already expanded or online DDL unsupported.
-- Keep legacy host available while Boot 4 Mapper reads host_name.
ALTER TABLE master_tenant
  ADD COLUMN host_name varchar(64) NULL COMMENT '数据库主机名',
  ADD COLUMN status char(1) NOT NULL DEFAULT '1' COMMENT '状态(1正常 2停止)',
  ADD COLUMN expiration_date datetime NULL COMMENT '到期日期',
  ALGORITHM=INSTANT, LOCK=DEFAULT;
