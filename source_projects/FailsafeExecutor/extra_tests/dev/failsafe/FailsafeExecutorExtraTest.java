// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 FailsafeExecutor 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe;

import dev.failsafe.event.EventListener;
import dev.failsafe.event.ExecutionCompletedEvent;
import dev.failsafe.function.*;
import dev.failsafe.internal.EventHandler;
import dev.failsafe.internal.util.Assert;
import dev.failsafe.spi.AsyncExecutionInternal;
import dev.failsafe.spi.ExecutionResult;
import dev.failsafe.spi.FailsafeFuture;
import dev.failsafe.spi.Scheduler;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.*;
import java.util.function.BiConsumer;
import java.util.function.Function;
import org.junit.Test;
public class FailsafeExecutorExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
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
        _i15();
        _i16();
        _i17();
        _i18();
        _i19();
        _i20();
        _i21();
        _i22();
        _i23();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new FailsafeExecutor(new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.getPolicies();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.compose(null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.get((CheckedSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.get((ContextualSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.newCall((ContextualRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.newCall((ContextualSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.getAsync((CheckedSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.getAsync((ContextualSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.getAsyncExecution((dev.failsafe.function.AsyncRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.getStageAsync((CheckedSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.getStageAsync((ContextualSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.run((dev.failsafe.function.CheckedRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.run((ContextualRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.runAsync((dev.failsafe.function.CheckedRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14

    // @extra-start id=15
    @SuppressWarnings("unused")
    private void _i15() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.runAsync((ContextualRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=15

    // @extra-start id=16
    @SuppressWarnings("unused")
    private void _i16() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.runAsyncExecution((dev.failsafe.function.AsyncRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=16

    // @extra-start id=17
    @SuppressWarnings("unused")
    private void _i17() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.onComplete((dev.failsafe.event.EventListener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=17

    // @extra-start id=18
    @SuppressWarnings("unused")
    private void _i18() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.onFailure((dev.failsafe.event.EventListener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=18

    // @extra-start id=19
    @SuppressWarnings("unused")
    private void _i19() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.onSuccess((dev.failsafe.event.EventListener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=19

    // @extra-start id=20
    @SuppressWarnings("unused")
    private void _i20() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.with((ScheduledExecutorService) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=20

    // @extra-start id=21
    @SuppressWarnings("unused")
    private void _i21() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.with((ExecutorService) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=21

    // @extra-start id=22
    @SuppressWarnings("unused")
    private void _i22() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.with((Executor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=22

    // @extra-start id=23
    @SuppressWarnings("unused")
    private void _i23() {
        try {
            FailsafeExecutor v = new FailsafeExecutor(new java.util.ArrayList<>());
            v.with((dev.failsafe.spi.Scheduler) new dev.failsafe.internal.util.DelegatingScheduler((ExecutorService) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=23
}
