// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ExtensionRequestData 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package org.java_websocket.extensions;

import java.util.LinkedHashMap;
import java.util.Map;
import org.junit.Test;
public class ExtensionRequestDataExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i2();
        _i4();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            ExtensionRequestData.parseExtensionRequest("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0


    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ExtensionRequestData v = ExtensionRequestData.parseExtensionRequest("");
            v.getExtensionName();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2


    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            ExtensionRequestData v = ExtensionRequestData.parseExtensionRequest("");
            v.getExtensionParameters();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4
}
