// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 TestIssues217 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.qatest.core.issues;

import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.listener.EventListener;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchBuilder;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchCondition;
import com.alibaba.jvm.sandbox.core.util.matcher.ExtFilterMatcher;
import com.alibaba.jvm.sandbox.core.util.matcher.Matcher;
import com.alibaba.jvm.sandbox.qatest.core.enhance.target.Calculator;
import com.alibaba.jvm.sandbox.qatest.core.enhance.target.MyCalculator;
import com.alibaba.jvm.sandbox.qatest.core.mock.EmptyModuleEventWatcher;
import org.junit.Assert;
import org.junit.Test;
import java.io.IOException;
import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;
public class TestIssues217ExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            TestIssues217 v = new TestIssues217();
            v.matchingComputerAnnotation();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            TestIssues217 v = new TestIssues217();
            v.matchingInheritedComputerAnnotation();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            TestIssues217 v = new TestIssues217();
            v.matching__TestA_or_TestB__Annotation();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2



}
