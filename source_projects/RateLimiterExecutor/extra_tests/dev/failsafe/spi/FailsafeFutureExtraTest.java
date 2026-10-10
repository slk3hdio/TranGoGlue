// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 FailsafeFuture 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.spi;

import dev.failsafe.ExecutionContext;
import java.util.Collections;
import java.util.Iterator;
import java.util.Map;
import java.util.Map.Entry;
import java.util.TreeMap;
import java.util.concurrent.CancellationException;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Future;
import java.util.function.BiConsumer;
import org.junit.Test;
public class FailsafeFutureExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
        _i6();
        _i7();
        _i9();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new FailsafeFuture((BiConsumer) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            FailsafeFuture v = new FailsafeFuture((BiConsumer) null);
            v.complete(null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            FailsafeFuture v = new FailsafeFuture((BiConsumer) null);
            v.completeExceptionally((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            FailsafeFuture v = new FailsafeFuture((BiConsumer) null);
            v.cancel(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            FailsafeFuture v = new FailsafeFuture((BiConsumer) null);
            v.completeResult(new ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4


    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            FailsafeFuture v = new FailsafeFuture((BiConsumer) null);
            v.setExecution((ExecutionInternal) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            FailsafeFuture v = new FailsafeFuture((BiConsumer) null);
            v.setCancelFn(0, (BiConsumer) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7


    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            FailsafeFuture v = new FailsafeFuture((BiConsumer) null);
            v.propagateCancellation((Future) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9
}
