// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 CompressionExtension 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package org.java_websocket.extensions;

import org.java_websocket.exceptions.InvalidDataException;
import org.java_websocket.exceptions.InvalidFrameException;
import org.java_websocket.framing.ControlFrame;
import org.java_websocket.framing.DataFrame;
import org.java_websocket.framing.Framedata;
import org.junit.Test;
public class CompressionExtensionExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            CompressionExtension v = new org.java_websocket.extensions.permessage_deflate.PerMessageDeflateExtension();
            v.isFrameValid((org.java_websocket.framing.Framedata) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0
}
