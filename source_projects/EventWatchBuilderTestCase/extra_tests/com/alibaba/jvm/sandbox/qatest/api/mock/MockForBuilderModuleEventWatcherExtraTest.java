// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 MockForBuilderModuleEventWatcher 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.qatest.api.mock;

import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.filter.Filter;
import com.alibaba.jvm.sandbox.api.listener.EventListener;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchCondition;
import com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;
public class MockForBuilderModuleEventWatcherExtraTest {
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
        _i10();
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.getEventWatchCondition();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.getEventListener();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.getProgress();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.getEventTypeArray();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.watch((com.alibaba.jvm.sandbox.api.filter.Filter) null, (com.alibaba.jvm.sandbox.api.listener.EventListener) null, (com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.Progress) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.watch((com.alibaba.jvm.sandbox.api.filter.Filter) null, (com.alibaba.jvm.sandbox.api.listener.EventListener) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.watch((com.alibaba.jvm.sandbox.api.listener.ext.EventWatchCondition) null, (com.alibaba.jvm.sandbox.api.listener.EventListener) null, (com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.Progress) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.delete(0, (com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.Progress) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7

    // @extra-start id=8
    @SuppressWarnings("unused")
    private void _i8() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.delete(0);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=8

    // @extra-start id=9
    @SuppressWarnings("unused")
    private void _i9() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.watching((com.alibaba.jvm.sandbox.api.filter.Filter) null, (com.alibaba.jvm.sandbox.api.listener.EventListener) null, (com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.Progress) null, (com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.WatchCallback) null, (com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.Progress) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=9

    // @extra-start id=10
    @SuppressWarnings("unused")
    private void _i10() {
        try {
            MockForBuilderModuleEventWatcher v = new MockForBuilderModuleEventWatcher();
            v.watching((com.alibaba.jvm.sandbox.api.filter.Filter) null, (com.alibaba.jvm.sandbox.api.listener.EventListener) null, (com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.WatchCallback) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=10
}
