// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 RateLimiterExecutor 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.internal;

import dev.failsafe.RateLimitExceededException;
import dev.failsafe.RateLimiter;
import dev.failsafe.spi.ExecutionResult;
import dev.failsafe.spi.FailsafeFuture;
import dev.failsafe.spi.PolicyExecutor;
import dev.failsafe.spi.Scheduler;
import java.time.Duration;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import org.junit.Test;
public class RateLimiterExecutorExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new RateLimiterExecutor((RateLimiterImpl) null, 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            RateLimiterExecutor v = new RateLimiterExecutor((RateLimiterImpl) null, 0);
            v.preExecute();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

}
