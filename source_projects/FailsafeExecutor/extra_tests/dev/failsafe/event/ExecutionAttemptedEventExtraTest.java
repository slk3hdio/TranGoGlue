// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ExecutionAttemptedEvent 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.event;

import dev.failsafe.ExecutionContext;
import org.junit.Test;
public class ExecutionAttemptedEventExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new ExecutionAttemptedEvent(null, (Throwable) null, (dev.failsafe.ExecutionContext) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            ExecutionAttemptedEvent v = new ExecutionAttemptedEvent(null, (Throwable) null, (dev.failsafe.ExecutionContext) null);
            v.getLastException();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ExecutionAttemptedEvent v = new ExecutionAttemptedEvent(null, (Throwable) null, (dev.failsafe.ExecutionContext) null);
            v.getLastResult();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ExecutionAttemptedEvent v = new ExecutionAttemptedEvent(null, (Throwable) null, (dev.failsafe.ExecutionContext) null);
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3
}
