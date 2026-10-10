// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 JSONParser 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package cn.hutool.json;

import cn.hutool.core.lang.Filter;
import cn.hutool.core.lang.mutable.Mutable;
import cn.hutool.core.lang.mutable.MutablePair;
import org.junit.Test;
public class JSONParserExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
        _i5();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            JSONParser.of((JSONTokener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            new JSONParser((JSONTokener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            JSONParser v = new JSONParser((JSONTokener) null);
            v.parseTo((JSONObject) null, (cn.hutool.core.lang.Filter) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            JSONParser v = JSONParser.of((JSONTokener) null);
            v.parseTo((JSONObject) null, (cn.hutool.core.lang.Filter) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            JSONParser v = new JSONParser((JSONTokener) null);
            v.parseTo((JSONArray) null, (cn.hutool.core.lang.Filter) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            JSONParser v = JSONParser.of((JSONTokener) null);
            v.parseTo((JSONArray) null, (cn.hutool.core.lang.Filter) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5
}
