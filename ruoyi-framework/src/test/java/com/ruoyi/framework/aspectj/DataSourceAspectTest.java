package com.ruoyi.framework.aspectj;

import com.ruoyi.common.annotation.DataSource;
import com.ruoyi.common.enums.DataSourceType;
import com.ruoyi.framework.datasource.DynamicDataSourceContextHolder;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.reflect.MethodSignature;
import org.junit.jupiter.api.AfterEach;
import org.junit.jupiter.api.Test;
import org.springframework.transaction.support.TransactionSynchronizationManager;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.Mockito.*;

class DataSourceAspectTest {

    @AfterEach
    void clear() {
        DynamicDataSourceContextHolder.clearDataSourceKey();
        if (TransactionSynchronizationManager.isSynchronizationActive()) {
            TransactionSynchronizationManager.clearSynchronization();
        }
        TransactionSynchronizationManager.setActualTransactionActive(false);
    }

    @Test
    void masterScopeRestoresOuterTenantOnSuccessAndFailure() throws Throwable {
        DynamicDataSourceContextHolder.setDataSourceKey("tenant-a");
        ProceedingJoinPoint success = point();
        when(success.proceed()).thenAnswer(invocation -> {
            assertEquals("MASTER", DynamicDataSourceContextHolder.getDataSourceKey());
            return "done";
        });
        assertEquals("done", new DataSourceAspect().around(success));
        assertEquals("tenant-a", DynamicDataSourceContextHolder.getDataSourceKey());

        ProceedingJoinPoint failure = point();
        when(failure.proceed()).thenThrow(new IllegalStateException("query failed"));
        assertThrows(IllegalStateException.class, () -> new DataSourceAspect().around(failure));
        assertEquals("tenant-a", DynamicDataSourceContextHolder.getDataSourceKey());
    }

    @Test
    void switchingInsideBoundTransactionFailsBeforeQuery() throws Throwable {
        DynamicDataSourceContextHolder.setDataSourceKey("tenant-a");
        TransactionSynchronizationManager.setActualTransactionActive(true);
        ProceedingJoinPoint point = point();
        assertThrows(IllegalStateException.class, () -> new DataSourceAspect().around(point));
        assertEquals("tenant-a", DynamicDataSourceContextHolder.getDataSourceKey());
        verify(point, never()).proceed();
    }

    @Test
    void switchingDuringSynchronizationOnlyScopeAlsoFailsClosed() throws Throwable {
        DynamicDataSourceContextHolder.setDataSourceKey("tenant-a");
        TransactionSynchronizationManager.initSynchronization();
        ProceedingJoinPoint point = point();
        assertThrows(IllegalStateException.class, () -> new DataSourceAspect().around(point));
        assertEquals("tenant-a", DynamicDataSourceContextHolder.getDataSourceKey());
        verify(point, never()).proceed();
    }

    private static ProceedingJoinPoint point() throws NoSuchMethodException {
        ProceedingJoinPoint point = mock(ProceedingJoinPoint.class);
        MethodSignature signature = mock(MethodSignature.class);
        when(point.getSignature()).thenReturn(signature);
        when(point.getTarget()).thenReturn(new AnnotatedService());
        when(signature.getMethod()).thenReturn(AnnotatedService.class.getMethod("readMaster"));
        when(signature.getDeclaringType()).thenReturn(AnnotatedService.class);
        return point;
    }

    public static final class AnnotatedService {
        @DataSource(DataSourceType.MASTER)
        public void readMaster() {
        }
    }
}
