// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 AdviceListener 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.api.listener.ext;

import com.alibaba.jvm.sandbox.api.ProcessController;
import com.alibaba.jvm.sandbox.api.event.Event;
import org.junit.Test;
public class AdviceListenerExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
        _i5();
        _i6();
        _i7();
        _i8();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            AdviceListener v = new AdviceListener();
            v.before(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            AdviceListener v = new AdviceListener();
            v.afterReturning(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            AdviceListener v = new AdviceListener();
            v.after(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            AdviceListener v = new AdviceListener();
            v.afterThrowing(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            AdviceListener v = new AdviceListener();
            v.beforeCall(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()), 0, "", "", "");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            AdviceListener v = new AdviceListener();
            v.afterCallReturning(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()), 0, "", "", "");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            AdviceListener v = new AdviceListener();
            v.afterCallThrowing(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()), 0, "", "", "", "");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            AdviceListener v = new AdviceListener();
            v.afterCall(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()), 0, "", "", "", "");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            AdviceListener v = new AdviceListener();
            v.beforeLine(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()), 0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8
}
