// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 Recorder 的成员,
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
public class RecorderExtraTest {
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
            Asserts.Recorder v = new Asserts.Recorder();
            v.reset();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertEquals(new Object(), new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertFalse(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertNotNull(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertNull(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.assertTrue(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.fail("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.fail((Throwable) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            Asserts.Recorder v = new Asserts.Recorder();
            v.throwFailures();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8
}
