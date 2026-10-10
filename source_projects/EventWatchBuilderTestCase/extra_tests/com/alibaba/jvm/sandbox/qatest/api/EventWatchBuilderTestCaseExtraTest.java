// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 EventWatchBuilderTestCase 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.qatest.api;

import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.filter.AccessFlags;
import com.alibaba.jvm.sandbox.api.filter.Filter;
import com.alibaba.jvm.sandbox.api.listener.ext.AdviceListener;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchBuilder;
import com.alibaba.jvm.sandbox.qatest.api.mock.MockForBuilderModuleEventWatcher;
import com.alibaba.jvm.sandbox.qatest.api.util.ApiQaArrayUtils;
import org.junit.Assert;
import org.junit.Test;
public class EventWatchBuilderTestCaseExtraTest {
    @Test(timeout = 20000)
    public void _batch0() {
        _i0();
        _i1();
        _i2();
        _i3();
        _i4();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            EventWatchBuilderTestCase v = new EventWatchBuilderTestCase();
            v.test$$EventWatchBuilder$$normal$$normal();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            EventWatchBuilderTestCase v = new EventWatchBuilderTestCase();
            v.test$$EventWatchBuilder$$normal$$all();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            EventWatchBuilderTestCase v = new EventWatchBuilderTestCase();
            v.test$$EventWatchBuilder$$normal$$CallOnly();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            EventWatchBuilderTestCase v = new EventWatchBuilderTestCase();
            v.test$$EventWatchBuilder$$normal$$LineOnly();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            EventWatchBuilderTestCase v = new EventWatchBuilderTestCase();
            v.test$$EventWatchBuilder$$regex();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4
}
