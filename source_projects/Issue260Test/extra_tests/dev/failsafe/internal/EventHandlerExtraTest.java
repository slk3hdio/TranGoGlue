// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 EventHandler 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.internal;

import dev.failsafe.event.EventListener;
import dev.failsafe.ExecutionContext;
import dev.failsafe.event.ExecutionAttemptedEvent;
import dev.failsafe.event.ExecutionCompletedEvent;
import dev.failsafe.event.ExecutionScheduledEvent;
import dev.failsafe.spi.ExecutionResult;
import java.time.Duration;
import org.junit.Test;
public class EventHandlerExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            EventHandler.ofExecutionCompleted((dev.failsafe.event.EventListener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            EventHandler.ofExecutionAttempted((dev.failsafe.event.EventListener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            EventHandler.ofExecutionScheduled((dev.failsafe.event.EventListener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2
}
