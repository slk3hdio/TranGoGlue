// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 ClassStructureByChildClassTestCase 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.qatest.core.util.matcher;

import com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure;
import com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructureFactory;
import com.alibaba.jvm.sandbox.qatest.core.util.matcher.asserts.BehaviorStructureAsserter;
import com.alibaba.jvm.sandbox.qatest.core.util.matcher.asserts.BehaviorStructureCollectionAsserter;
import com.alibaba.jvm.sandbox.qatest.core.util.matcher.asserts.ClassStructureAsserter;
import com.alibaba.jvm.sandbox.qatest.core.util.matcher.target.ChildClass;
import org.apache.commons.lang3.StringUtils;
import org.junit.Test;
import org.junit.runner.RunWith;
import org.junit.runners.Parameterized;
import java.io.IOException;
import java.util.Collection;
public class ClassStructureByChildClassTestCaseExtraTest {
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
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            ClassStructureByChildClassTestCase.getData();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure$$methodOfReturn();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure$$methodOfSingleArguments();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure$$methodOfArrayArguments();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure$$methodOfChildClassWithAnnotation();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure$$methodOfPrivateStatic();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure$$methodOfPrivateNative();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            ClassStructureByChildClassTestCase v = new ClassStructureByChildClassTestCase((com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure) null);
            v.test$$ChildClassStructure$$methodOfParentInterfaceFirstFirstWithAnnotation();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9
}
