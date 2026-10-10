// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 CompositeError 的成员,
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
public class CompositeErrorExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new Asserts.CompositeError(new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            Asserts.CompositeError v = new Asserts.CompositeError(new java.util.ArrayList<>());
            v.getMessage();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1
}
