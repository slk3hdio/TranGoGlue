// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 Timeout 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe;

import dev.failsafe.event.EventListener;
import dev.failsafe.function.AsyncRunnable;
import dev.failsafe.internal.TimeoutImpl;
import dev.failsafe.internal.util.Assert;
import java.time.Duration;
import org.junit.Test;
public class TimeoutExtraTest {
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
            Timeout.builder((Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            Timeout.builder(new TimeoutConfig(new TimeoutConfig((TimeoutConfig) null)));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            Timeout.of((Duration) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2
}
