// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 BehaviorStructure 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.core.util.matcher.structure;

import com.alibaba.jvm.sandbox.api.util.LazyGet;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.List;
import org.junit.Test;
public class BehaviorStructureExtraTest {
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
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.getReturnTypeClassStructure();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.getParameterTypeClassStructures();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.getExceptionTypeClassStructures();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.getAnnotationTypeClassStructures();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.getSignCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.toString();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.hashCode();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            BehaviorStructure v = new BehaviorStructure((Access) null, "", (ClassStructure) null, (ClassStructure) null, new java.util.ArrayList<>(), new java.util.ArrayList<>(), new java.util.ArrayList<>());
            v.equals(new Object());
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8
}
