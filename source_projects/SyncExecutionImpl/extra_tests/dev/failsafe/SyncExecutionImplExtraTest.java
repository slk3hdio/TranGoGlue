// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 SyncExecutionImpl 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe;

import dev.failsafe.spi.ExecutionResult;
import dev.failsafe.spi.PolicyExecutor;
import dev.failsafe.spi.Scheduler;
import dev.failsafe.spi.SyncExecutionInternal;
import java.time.Duration;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.Test;
public class SyncExecutionImplExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i2();
        _i3();
        _i4();
        _i5();
        _i6();
        _i7();
        _i8();
        _i9();
        _i10();
        _i11();
        _i12();
        _i13();
        _i14();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new SyncExecutionImpl(new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0


    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.complete();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.isComplete();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.getDelay();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.record(null, (Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.recordResult(null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.recordException((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.preExecute();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.postExecute(new dev.failsafe.spi.ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.isInterrupted();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.setInterruptable(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.interrupt();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.copy();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            SyncExecutionImpl v = new SyncExecutionImpl(new java.util.ArrayList<>());
            v.executeSync();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14
}
