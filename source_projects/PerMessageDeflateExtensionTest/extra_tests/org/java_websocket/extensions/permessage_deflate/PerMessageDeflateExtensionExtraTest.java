// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 PerMessageDeflateExtension 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package org.java_websocket.extensions.permessage_deflate;

import java.io.ByteArrayOutputStream;
import java.nio.ByteBuffer;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.zip.DataFormatException;
import java.util.zip.Deflater;
import java.util.zip.Inflater;
import org.java_websocket.enums.Opcode;
import org.java_websocket.exceptions.InvalidDataException;
import org.java_websocket.exceptions.InvalidFrameException;
import org.java_websocket.extensions.CompressionExtension;
import org.java_websocket.extensions.ExtensionRequestData;
import org.java_websocket.extensions.IExtension;
import org.java_websocket.framing.CloseFrame;
import org.java_websocket.framing.ContinuousFrame;
import org.java_websocket.framing.DataFrame;
import org.java_websocket.framing.Framedata;
import org.java_websocket.framing.FramedataImpl1;
import org.junit.Test;
public class PerMessageDeflateExtensionExtraTest {
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
            new PerMessageDeflateExtension();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            new PerMessageDeflateExtension(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.getCompressionLevel();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.getThreshold();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.setThreshold(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.isServerNoContextTakeover();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.setServerNoContextTakeover(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.isClientNoContextTakeover();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.setClientNoContextTakeover(false);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.decodeFrame((org.java_websocket.framing.Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.encodeFrame((org.java_websocket.framing.Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10

    // @extra-start id=11
    @SuppressWarnings("unused")
    private void _i11() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.acceptProvidedExtensionAsServer("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=11

    // @extra-start id=12
    @SuppressWarnings("unused")
    private void _i12() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.acceptProvidedExtensionAsClient("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=12

    // @extra-start id=13
    @SuppressWarnings("unused")
    private void _i13() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.getProvidedExtensionAsClient();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=13

    // @extra-start id=14
    @SuppressWarnings("unused")
    private void _i14() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.getProvidedExtensionAsServer();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=14

    // @extra-start id=15
    @SuppressWarnings("unused")
    private void _i15() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.copyInstance();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=15

    // @extra-start id=16
    @SuppressWarnings("unused")
    private void _i16() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.isFrameValid((org.java_websocket.framing.Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=16

    // @extra-start id=17
    @SuppressWarnings("unused")
    private void _i17() {
        try {
            PerMessageDeflateExtension v = new PerMessageDeflateExtension();
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=17
}
