package com.ruoyi.framework.aspectj;

import java.util.Objects;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Pointcut;
import org.aspectj.lang.reflect.MethodSignature;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.core.annotation.AnnotationUtils;
import org.springframework.core.annotation.Order;
import org.springframework.aop.support.AopUtils;
import org.springframework.stereotype.Component;
import org.springframework.transaction.support.TransactionSynchronizationManager;
import com.ruoyi.common.annotation.DataSource;
import com.ruoyi.framework.datasource.DynamicDataSourceContextHolder;

/**
 * 多数据源处理
 * 
 * @author ruoyi
 */
@Aspect
@Order(1)
@Component
public class DataSourceAspect
{
    protected Logger logger = LoggerFactory.getLogger(getClass());

    @Pointcut("@annotation(com.ruoyi.common.annotation.DataSource)"
            + "|| @within(com.ruoyi.common.annotation.DataSource)")
    public void dsPointCut()
    {

    }

    @Around("dsPointCut()")
    public Object around(ProceedingJoinPoint point) throws Throwable
    {
        DataSource dataSource = getDataSource(point);
        if (dataSource == null)
        {
            return point.proceed();
        }

        String previous = DynamicDataSourceContextHolder.getDataSourceKey();
        String requested = dataSource.value().name();
        if (!requested.equals(previous) && (TransactionSynchronizationManager.isActualTransactionActive()
                || TransactionSynchronizationManager.isSynchronizationActive()))
        {
            throw new IllegalStateException("Cannot switch data source inside an active transaction");
        }

        DynamicDataSourceContextHolder.setDataSourceKey(requested);

        try
        {
            return point.proceed();
        }
        finally
        {
            // Restore the outer tenant scope after a nested MASTER call.
            if (previous == null)
            {
                DynamicDataSourceContextHolder.clearDataSourceKey();
            }
            else
            {
                DynamicDataSourceContextHolder.setDataSourceKey(previous);
            }
        }
    }

    /**
     * 获取需要切换的数据源
     */
    public DataSource getDataSource(ProceedingJoinPoint point)
    {
        MethodSignature signature = (MethodSignature) point.getSignature();
        Class<?> targetClass = point.getTarget().getClass();
        DataSource dataSource = AnnotationUtils.findAnnotation(
                AopUtils.getMostSpecificMethod(signature.getMethod(), targetClass), DataSource.class);
        if (Objects.nonNull(dataSource))
        {
            return dataSource;
        }

        dataSource = AnnotationUtils.findAnnotation(signature.getMethod(), DataSource.class);
        if (Objects.nonNull(dataSource))
        {
            return dataSource;
        }
        dataSource = AnnotationUtils.findAnnotation(targetClass, DataSource.class);
        return dataSource != null ? dataSource
                : AnnotationUtils.findAnnotation(signature.getDeclaringType(), DataSource.class);
    }
}
