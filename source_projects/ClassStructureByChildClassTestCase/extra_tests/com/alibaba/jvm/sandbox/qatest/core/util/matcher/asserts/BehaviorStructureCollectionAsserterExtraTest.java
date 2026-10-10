// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 BehaviorStructureCollectionAsserter 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.qatest.core.util.matcher.asserts;

import com.alibaba.jvm.sandbox.core.util.matcher.structure.BehaviorStructure;
import org.apache.commons.lang3.ArrayUtils;
import org.junit.Test;
public class BehaviorStructureCollectionAsserterExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i5();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            BehaviorStructureCollectionAsserter.buildBehaviorSignCodeArrayAsserter();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0





    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            BehaviorStructureCollectionAsserter v = BehaviorStructureCollectionAsserter.buildBehaviorSignCodeArrayAsserter();
            v.assertTargetByKey("", (Asserter) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5
}
