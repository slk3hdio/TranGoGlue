// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 TimeoutExceededException 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe;

import org.junit.Test;
public class TimeoutExceededExceptionExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new TimeoutExceededException((Timeout) new dev.failsafe.internal.TimeoutImpl(new TimeoutConfig((TimeoutConfig) null)));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            TimeoutExceededException v = new TimeoutExceededException((Timeout) new dev.failsafe.internal.TimeoutImpl((TimeoutConfig) null));
            v.getTimeout();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1
}
