// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ExecutionImpl 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe;

import dev.failsafe.function.CheckedRunnable;
import dev.failsafe.internal.util.Assert;
import dev.failsafe.spi.ExecutionInternal;
import dev.failsafe.spi.ExecutionResult;
import dev.failsafe.spi.PolicyExecutor;
import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.ListIterator;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
public class ExecutionImplExtraTest {
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
        _i24();
    }

    @Test(timeout = 20000)
    public void _batch1() {
        _i25();
        _i26();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new ExecutionImpl(new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            new ExecutionImpl(new ExecutionImpl(new java.util.ArrayList<>()));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            new ExecutionImpl(new dev.failsafe.spi.ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.onCancel((dev.failsafe.function.CheckedRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.preExecute();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.isPreExecuted();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.recordAttempt();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.record(new dev.failsafe.spi.ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.postExecute(new dev.failsafe.spi.ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.cancel();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.cancel((dev.failsafe.spi.PolicyExecutor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.isCancelled();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.isCancelled((dev.failsafe.spi.PolicyExecutor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getLock();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14

    // @extra-start id=15
    @SuppressWarnings("unused")
    private void _i15() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getLatest();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=15

    // @extra-start id=16
    @SuppressWarnings("unused")
    private void _i16() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getElapsedTime();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=16

    // @extra-start id=17
    @SuppressWarnings("unused")
    private void _i17() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getElapsedAttemptTime();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=17

    // @extra-start id=18
    @SuppressWarnings("unused")
    private void _i18() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getAttemptCount();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=18

    // @extra-start id=19
    @SuppressWarnings("unused")
    private void _i19() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getExecutionCount();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=19

    // @extra-start id=20
    @SuppressWarnings("unused")
    private void _i20() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getLastException();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=20

    // @extra-start id=21
    @SuppressWarnings("unused")
    private void _i21() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getLastResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=21

    // @extra-start id=22
    @SuppressWarnings("unused")
    private void _i22() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getLastResult(null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=22

    // @extra-start id=23
    @SuppressWarnings("unused")
    private void _i23() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.getStartTime();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=23

    // @extra-start id=24
    @SuppressWarnings("unused")
    private void _i24() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.isFirstAttempt();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=24

    // @extra-start id=25
    @SuppressWarnings("unused")
    private void _i25() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.isRetry();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=25

    // @extra-start id=26
    @SuppressWarnings("unused")
    private void _i26() {
        try {
            ExecutionImpl v = new ExecutionImpl(new java.util.ArrayList<>());
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=26
}
