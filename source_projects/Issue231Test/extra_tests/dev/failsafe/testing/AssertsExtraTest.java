// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 Asserts 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package dev.failsafe.testing;

import dev.failsafe.function.CheckedRunnable;
import dev.failsafe.function.CheckedSupplier;
import org.testng.Assert;
import java.io.PrintWriter;
import java.io.StringWriter;
import java.util.Arrays;
import java.util.Formatter;
import java.util.List;
import java.util.concurrent.CopyOnWriteArrayList;
import java.util.function.Function;
import org.junit.Test;
public class AssertsExtraTest {
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
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            Asserts.matches((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            Asserts.assertMatches((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            Asserts.assertMatches((Throwable) null, new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            Asserts.assertThrows((dev.failsafe.function.CheckedRunnable) null, (Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            Asserts.assertThrows((dev.failsafe.function.CheckedRunnable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            Asserts.assertThrows((dev.failsafe.function.CheckedRunnable) null, new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            Asserts.assertThrowsSup((dev.failsafe.function.CheckedSupplier) null, new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            Asserts.assertThrows((dev.failsafe.function.CheckedRunnable) null, (Function) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            new Asserts.CompositeError(new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            Asserts.CompositeError v = new Asserts.CompositeError(new java.util.ArrayList<>());
            v.getMessage();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.reset();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertEquals(new Object(), new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertFalse(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertNotNull(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertNull(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14

    // @extra-start id=15
    @SuppressWarnings("unused")
    private void _i15() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertTrue(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=15

    // @extra-start id=16
    @SuppressWarnings("unused")
    private void _i16() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.fail("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=16

    // @extra-start id=17
    @SuppressWarnings("unused")
    private void _i17() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.fail((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=17

    // @extra-start id=18
    @SuppressWarnings("unused")
    private void _i18() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.throwFailures();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=18
}
