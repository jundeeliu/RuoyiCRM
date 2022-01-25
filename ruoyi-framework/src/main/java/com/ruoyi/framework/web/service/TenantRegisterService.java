package com.ruoyi.framework.web.service;

import com.ruoyi.common.exception.ServiceException;
import com.ruoyi.common.utils.DateUtils;
import com.ruoyi.common.utils.SecurityUtils;
import com.ruoyi.common.utils.SnowflakeIdWorker;
import com.ruoyi.common.utils.uuid.ShortUUID;
import com.ruoyi.tenant.dto.TenantDatabaseDTO;
import com.ruoyi.tenant.form.TenantRegisterForm;
import lombok.extern.slf4j.Slf4j;
import org.apache.ibatis.io.Resources;
import org.apache.ibatis.jdbc.ScriptRunner;
import org.apache.ibatis.jdbc.SqlRunner;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import java.sql.Connection;
import java.sql.DriverManager;
import java.sql.SQLException;
import java.sql.Statement;

/**
 * @Author: devjd
 * @Date: 2022/1/22
 * @Description:
 */
@Component
@Slf4j
public class TenantRegisterService {

    @Value("${tenant.database.host}")
    private String host;

    @Value("${tenant.database.port}")
    private String port;

    @Value("${tenant.database.username}")
    private String username;

    @Value("${tenant.database.password}")
    private String password;

    @Value("${tenant.prefix}")
    private String prefix;

    private String getUrl(){
        String url="jdbc:mysql://"+host+":"+port+"/";
        return url;
    }

    /**
     * 获取数据库连接
     */
    private Connection getConnection() throws SQLException {

        return DriverManager.getConnection(getUrl(), username, password);
    }


    public TenantDatabaseDTO initDatabase(TenantRegisterForm form) throws Exception {
        Connection conn = getConnection();
        Statement stmt = null;
        TenantDatabaseDTO tenantDatabaseDTO = null;
        //创建数据库ID
        String tenantDatabaseID = ShortUUID.nextID();
        //组合数据库名
        String tenantDatabase = prefix + tenantDatabaseID;
        try {
            conn.setAutoCommit(false);
            stmt = conn.createStatement();

            // 创建库
            String createDatabaseSQL = "CREATE DATABASE IF NOT EXISTS `" + tenantDatabase + "` DEFAULT CHARSET utf8mb4 COLLATE utf8mb4_general_ci;";
            stmt.execute(createDatabaseSQL);

            //创建数据库用户名及密码
            String tenantDatabaseUsername = tenantDatabase;
            String tenantDatabasePassword = ShortUUID.nextID();

            //用户授权
            String grantSQL = "GRANT select, insert, update, delete ON "+tenantDatabase+".* TO '" + tenantDatabaseUsername + "'@'localhost' IDENTIFIED BY '"+tenantDatabasePassword+"'";
            stmt.execute(grantSQL);

            // 切换到
            conn.setCatalog(tenantDatabase);

            // 获取当前数据库名称
            log.info("当前数据库：{}", conn.getCatalog()); // 若未选择数据库，则 getCatalog 返回空
            conn.getCatalog();

            //创建返回对象
            tenantDatabaseDTO = new TenantDatabaseDTO();
            tenantDatabaseDTO.setTenantDatabase(tenantDatabase);
            tenantDatabaseDTO.setTenantName(form.tenantName);
            tenantDatabaseDTO.setDbUser(tenantDatabaseUsername);
            tenantDatabaseDTO.setDbPass(tenantDatabasePassword);
            tenantDatabaseDTO.setAdminName(form.adminName);
            tenantDatabaseDTO.setAdminPass(form.adminPass);
            String tenantUrl = getUrl() + tenantDatabaseDTO.tenantDatabase + "?useUnicode=true&characterEncoding=utf8&zeroDateTimeBehavior=convertToNull&useSSL=true&serverTimezone=GMT%2B8";
            tenantDatabaseDTO.setUrl(tenantUrl);

            //执行初始化脚本
            executeInitScript(conn, tenantDatabaseDTO);

        } catch (Exception ex){
            ex.printStackTrace();


            //删除数据库
            stmt.execute("DROP DATABASE IF EXISTS "+ tenantDatabase);
            log.error("删除数据库:{}",tenantDatabase );

            throw new ServiceException("执行数据库操作时发生错误");
        }finally{
            if (stmt != null) {
                stmt.close();
            }
            conn.close();
        }
        return tenantDatabaseDTO;
    }

    private void executeInitScript(Connection conn, TenantDatabaseDTO tenantDatabaseDTO) throws SQLException {
        try {
            ScriptRunner runner = new ScriptRunner(conn);
            runner.setErrorLogWriter(null);
            runner.setLogWriter(null);

            runner.runScript(Resources.getResourceAsReader("init-sql-script/rycrm-tenant-sample.sql"));

            SqlRunner sqlRunner = new SqlRunner(conn);
            String insertSql;

            //插入部门
            insertSql = "INSERT INTO sys_dept VALUES (100, 0, '0', '" + tenantDatabaseDTO.tenantName + "', 0, '" + tenantDatabaseDTO.tenantName + "', '00000000000', 'admin@admin.com', '0', '0', 'admin', '" + DateUtils.getTime() + "', 'admin', '" + DateUtils.getTime() + "');";
            sqlRunner.run(insertSql);

            //生成密码
            String encryptPassword = SecurityUtils.encryptPassword(tenantDatabaseDTO.adminPass);
            //插入系统超级管理员
            insertSql = "INSERT INTO sys_user (`user_id`, `dept_id`, `user_name`, `nick_name`, `user_type`, `email`, `phonenumber`, `sex`, `avatar`, `password`, `status`, `del_flag`, `login_ip`, `login_date`, `create_by`, `create_time`, `update_by`, `update_time`, `remark`) " +
                    "VALUES (1, 100, '" + tenantDatabaseDTO.adminName + "', '管理员', '00', 'admin@admin.com', '00000000000', '1', '', '" + encryptPassword + "', '0', '0', '127.0.0.1', '" + DateUtils.getTime() + "', '" + tenantDatabaseDTO.adminName + "', '" + DateUtils.getTime() + "', '', '" + DateUtils.getTime() + "', '管理员');";
            sqlRunner.run(insertSql);

            conn.commit();

        } catch (SQLException e) {
            e.printStackTrace();
            conn.rollback();
            throw new ServiceException("初始化用户数据脚本时出错");
        }catch (Exception ex){
            ex.printStackTrace();
            throw new ServiceException("执行初始用户数据时出错");
        }

    }

    private String generateTenantDatabaseID() {
        SnowflakeIdWorker idWorker = new SnowflakeIdWorker(0, 0);
        long l = idWorker.nextId();
        return String.valueOf(l);
    }

}

