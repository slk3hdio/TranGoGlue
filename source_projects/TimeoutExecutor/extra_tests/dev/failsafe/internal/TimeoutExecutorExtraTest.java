// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 TimeoutExecutor 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.internal;

import dev.failsafe.Timeout;
import dev.failsafe.TimeoutConfig;
import dev.failsafe.TimeoutExceededException;
import dev.failsafe.spi.*;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicReference;
import java.util.function.Function;
import org.junit.Test;
public class TimeoutExecutorExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i1();
    }


    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            TimeoutExecutor v = new TimeoutExecutor(new TimeoutImpl((dev.failsafe.TimeoutConfig) null), 0);
            v.isFailure(new dev.failsafe.spi.ExecutionResult(null, (Throwable) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1


}
