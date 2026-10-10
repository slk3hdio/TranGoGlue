// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 UndeclaredThrowableStrategy 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package net.sf.cglib.transform.impl;

import net.sf.cglib.core.ClassGenerator;
import net.sf.cglib.core.DefaultGeneratorStrategy;
import net.sf.cglib.core.GeneratorStrategy;
import net.sf.cglib.core.TypeUtils;
import net.sf.cglib.transform.ClassTransformer;
import net.sf.cglib.transform.MethodFilter;
import net.sf.cglib.transform.MethodFilterTransformer;
import net.sf.cglib.transform.TransformingClassGenerator;
import org.junit.Test;
public class UndeclaredThrowableStrategyExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new UndeclaredThrowableStrategy(Object.class);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            UndeclaredThrowableStrategy v = new UndeclaredThrowableStrategy(Object.class);
            v.transform((net.sf.cglib.core.ClassGenerator) new net.sf.cglib.transform.TransformingClassGenerator((net.sf.cglib.core.ClassGenerator) new net.sf.cglib.transform.TransformingClassGenerator((net.sf.cglib.core.ClassGenerator) null, (net.sf.cglib.transform.ClassTransformer) null), (net.sf.cglib.transform.ClassTransformer) null));
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1
}
