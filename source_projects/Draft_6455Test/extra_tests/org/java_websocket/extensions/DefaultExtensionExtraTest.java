// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 DefaultExtension 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package org.java_websocket.extensions;

import org.java_websocket.exceptions.InvalidDataException;
import org.java_websocket.exceptions.InvalidFrameException;
import org.java_websocket.framing.Framedata;
import org.junit.Test;
public class DefaultExtensionExtraTest {
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
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.decodeFrame((org.java_websocket.framing.Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.encodeFrame((org.java_websocket.framing.Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.acceptProvidedExtensionAsServer("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.acceptProvidedExtensionAsClient("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.isFrameValid((org.java_websocket.framing.Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.getProvidedExtensionAsClient();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.getProvidedExtensionAsServer();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.copyInstance();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.reset();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.hashCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            DefaultExtension v = new DefaultExtension();
            v.equals(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11
}
