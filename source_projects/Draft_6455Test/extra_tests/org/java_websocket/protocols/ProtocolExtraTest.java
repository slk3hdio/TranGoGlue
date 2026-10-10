// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 Protocol 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package org.java_websocket.protocols;

import java.util.regex.Pattern;
import org.junit.Test;
public class ProtocolExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
        _i5();
        _i6();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new Protocol("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            Protocol v = new Protocol("");
            v.acceptProvidedProtocol("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            Protocol v = new Protocol("");
            v.getProvidedProtocol();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            Protocol v = new Protocol("");
            v.copyInstance();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            Protocol v = new Protocol("");
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            Protocol v = new Protocol("");
            v.equals(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            Protocol v = new Protocol("");
            v.hashCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6
}
