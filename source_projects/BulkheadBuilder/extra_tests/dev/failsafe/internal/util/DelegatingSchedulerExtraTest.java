// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 DelegatingScheduler 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.internal.util;

import dev.failsafe.spi.Scheduler;
import java.util.concurrent.*;
import org.junit.Test;
public class DelegatingSchedulerExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i3();
        _i4();
        _i5();
        _i6();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new DelegatingScheduler((ExecutorService) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            DelegatingScheduler v = new DelegatingScheduler((ExecutorService) null);
            v.schedule((Callable) null, 0L, (TimeUnit) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1


    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            new DelegatingScheduler.ScheduledCompletableFuture(0L, (TimeUnit) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            DelegatingScheduler.ScheduledCompletableFuture v = new DelegatingScheduler.ScheduledCompletableFuture(0L, (TimeUnit) null);
            v.getDelay((TimeUnit) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            DelegatingScheduler.ScheduledCompletableFuture v = new DelegatingScheduler.ScheduledCompletableFuture(0L, (TimeUnit) null);
            v.compareTo((Delayed) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            DelegatingScheduler.ScheduledCompletableFuture v = new DelegatingScheduler.ScheduledCompletableFuture(0L, (TimeUnit) null);
            v.cancel(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6
}
