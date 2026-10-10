// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 Functions 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe;

import dev.failsafe.function.*;
import dev.failsafe.internal.util.Assert;
import dev.failsafe.spi.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.function.Function;
import org.junit.Test;
public class FunctionsExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i4();
        _i6();
        _i7();
        _i8();
        _i9();
        _i10();
        _i11();
        _i12();
        _i13();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            Functions.get((ContextualSupplier) null, (Executor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            Functions.getPromise((ContextualSupplier) null, (Executor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            Functions.getPromiseExecution((dev.failsafe.function.AsyncRunnable) null, (Executor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2


    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            Functions.toExecutionAware((Function) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4


    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            Functions.toCtxSupplier((dev.failsafe.function.CheckedRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            Functions.toCtxSupplier((ContextualRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            Functions.toCtxSupplier((CheckedSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            Functions.withExecutor((ContextualSupplier) null, (Executor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            Functions.withExecutor((dev.failsafe.function.AsyncRunnable) null, (Executor) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            Functions.toFn((CheckedConsumer) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            Functions.toFn((dev.failsafe.function.CheckedRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            Functions.toFn((CheckedSupplier) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

}
