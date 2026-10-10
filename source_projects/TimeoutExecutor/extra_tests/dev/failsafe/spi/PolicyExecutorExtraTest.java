// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 PolicyExecutor 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.spi;

import dev.failsafe.ExecutionContext;
import dev.failsafe.Policy;
import dev.failsafe.internal.EventHandler;
import java.util.concurrent.CompletableFuture;
import java.util.function.Function;
import org.junit.Test;
public class PolicyExecutorExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i5();
        _i7();
        _i8();
        _i9();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            PolicyExecutor v = new dev.failsafe.internal.TimeoutExecutor(new dev.failsafe.internal.TimeoutImpl((dev.failsafe.TimeoutConfig) null), 0);
            v.getPolicyIndex();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            PolicyExecutor v = new dev.failsafe.internal.TimeoutExecutor(new dev.failsafe.internal.TimeoutImpl((dev.failsafe.TimeoutConfig) null), 0);
            v.preExecute();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1




    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            PolicyExecutor v = new dev.failsafe.internal.TimeoutExecutor(new dev.failsafe.internal.TimeoutImpl((dev.failsafe.TimeoutConfig) null), 0);
            v.postExecute((ExecutionInternal) null, new ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5


    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            PolicyExecutor v = new dev.failsafe.internal.TimeoutExecutor(new dev.failsafe.internal.TimeoutImpl((dev.failsafe.TimeoutConfig) null), 0);
            v.isFailure(new ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            PolicyExecutor v = new dev.failsafe.internal.TimeoutExecutor(new dev.failsafe.internal.TimeoutImpl((dev.failsafe.TimeoutConfig) null), 0);
            v.onSuccess(new ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            PolicyExecutor v = new dev.failsafe.internal.TimeoutExecutor(new dev.failsafe.internal.TimeoutImpl((dev.failsafe.TimeoutConfig) null), 0);
            v.onFailure((dev.failsafe.ExecutionContext) null, new ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

}
