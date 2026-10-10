// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 FramedataImpl1 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package org.java_websocket.framing;

import java.nio.ByteBuffer;
import org.java_websocket.enums.Opcode;
import org.java_websocket.exceptions.InvalidDataException;
import org.java_websocket.util.ByteBufferUtils;
import org.junit.Test;
public class FramedataImpl1ExtraTest {
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
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.isRSV1();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.isRSV2();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.isRSV3();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.isFin();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.getOpcode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.getTransfereMasked();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.getPayloadData();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.append((Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.setPayload((ByteBuffer) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.setFin(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.setRSV1(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.setRSV2(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.setRSV3(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14

    // @extra-start id=15
    @SuppressWarnings("unused")
    private void _i15() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.setTransferemasked(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=15

    // @extra-start id=16
    @SuppressWarnings("unused")
    private void _i16() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.equals(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=16

    // @extra-start id=17
    @SuppressWarnings("unused")
    private void _i17() {
        try {
            FramedataImpl1 v = FramedataImpl1.get(org.java_websocket.enums.Opcode.CONTINUOUS);
            v.hashCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=17
}
