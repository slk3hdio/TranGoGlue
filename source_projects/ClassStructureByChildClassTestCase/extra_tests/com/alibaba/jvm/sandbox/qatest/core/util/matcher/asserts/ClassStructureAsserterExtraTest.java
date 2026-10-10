// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ClassStructureAsserter 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.qatest.core.util.matcher.asserts;

import com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure;
import com.alibaba.jvm.sandbox.qatest.core.util.matcher.asserts.AccessAsserter.AccessIsEnum;
import org.junit.Test;
public class ClassStructureAsserterExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i10();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            ClassStructureAsserter v = new ClassStructureAsserter();
            v.assertAccess();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            ClassStructureAsserter v = new ClassStructureAsserter();
            v.assertJavaClassNameEquals("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ClassStructureAsserter v = new ClassStructureAsserter();
            v.assertSuper(new ClassStructureAsserter());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2








    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            ClassStructureAsserter v = new ClassStructureAsserter();
            v.assertThat("", (com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10
}
