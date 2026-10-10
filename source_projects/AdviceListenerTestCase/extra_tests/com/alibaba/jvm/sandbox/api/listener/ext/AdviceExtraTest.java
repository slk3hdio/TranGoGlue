// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 Advice 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.api.listener.ext;

import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.event.InvokeEvent;
import com.alibaba.jvm.sandbox.api.util.LazyGet;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.Test;
public class AdviceExtraTest {
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
        _i9();
        _i10();
        _i11();
        _i12();
        _i13();
        _i14();
        _i15();
        _i16();
        _i17();
        _i18();
        _i19();
        _i20();
        _i21();
        _i22();
        _i23();
        _i24();
    }

    @Test(timeout = 20000)
    public void _batch1() {
        _i25();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.applyBefore(new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()), new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object()));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.applyReturn(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.applyThrows((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.isReturn();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.isThrows();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.changeParameter(0, new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getProcessId();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getInvokeId();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getBehavior();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getLoader();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getParameterArray();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getTarget();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getReturnObj();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getThrowable();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14

    // @extra-start id=15
    @SuppressWarnings("unused")
    private void _i15() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.attach(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=15

    // @extra-start id=16
    @SuppressWarnings("unused")
    private void _i16() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.attachment();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=16

    // @extra-start id=17
    @SuppressWarnings("unused")
    private void _i17() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.hashCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=17

    // @extra-start id=18
    @SuppressWarnings("unused")
    private void _i18() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.equals(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=18

    // @extra-start id=19
    @SuppressWarnings("unused")
    private void _i19() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.mark("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=19

    // @extra-start id=20
    @SuppressWarnings("unused")
    private void _i20() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.hasMark("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=20

    // @extra-start id=21
    @SuppressWarnings("unused")
    private void _i21() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.unMark("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=21

    // @extra-start id=22
    @SuppressWarnings("unused")
    private void _i22() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.attach(new Object(), "");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=22

    // @extra-start id=23
    @SuppressWarnings("unused")
    private void _i23() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.isProcessTop();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=23

    // @extra-start id=24
    @SuppressWarnings("unused")
    private void _i24() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.getProcessTop();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=24

    // @extra-start id=25
    @SuppressWarnings("unused")
    private void _i25() {
        try {
            Advice v = new Advice(0, 0, (com.alibaba.jvm.sandbox.api.util.LazyGet) null, (ClassLoader) null, new Object[0], new Object());
            v.listHasMarkOnChain("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=25
}
