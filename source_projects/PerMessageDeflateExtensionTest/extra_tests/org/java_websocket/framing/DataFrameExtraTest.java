// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 DataFrame 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package org.java_websocket.framing;

import org.java_websocket.enums.Opcode;
import org.java_websocket.exceptions.InvalidDataException;
import org.junit.Test;
public class DataFrameExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            DataFrame v = new ContinuousFrame();
            v.isValid();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0
}
