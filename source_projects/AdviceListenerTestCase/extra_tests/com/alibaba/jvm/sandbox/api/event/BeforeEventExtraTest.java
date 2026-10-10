// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 BeforeEvent 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.api.event;

import org.junit.Test;
public class BeforeEventExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new BeforeEvent(0, 0, (ClassLoader) null, "", "", "", new Object(), new Object[0]);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            BeforeEvent v = new BeforeEvent(0, 0, (ClassLoader) null, "", "", "", new Object(), new Object[0]);
            v.changeParameter(0, new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1
}
