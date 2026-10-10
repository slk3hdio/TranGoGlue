// 自动生成的覆盖率补充测试(第三批, 与 tests/ 与 additional_tests/ 隔离), 勿手工修改。
// 由 gen_extra_tests.py 生成: 以默认参数逐一调用 EventWatchBuilder 的成员,
// 全部调用以 try/catch 包裹, 仅用于执行级覆盖统计。
package com.alibaba.jvm.sandbox.api.listener.ext;

import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.filter.AccessFlags;
import com.alibaba.jvm.sandbox.api.filter.ExtFilter;
import com.alibaba.jvm.sandbox.api.filter.ExtFilterImplByV140;
import com.alibaba.jvm.sandbox.api.filter.Filter;
import com.alibaba.jvm.sandbox.api.listener.EventListener;
import com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher;
import com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher.Progress;
import com.alibaba.jvm.sandbox.api.util.GaArrayUtils;
import com.alibaba.jvm.sandbox.api.util.GaStringUtils;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import org.junit.Test;
public class EventWatchBuilderExtraTest {
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
    }

    @Test(timeout = 20000)
    public void _batch1() {
    }

    @Test(timeout = 20000)
    public void _batch2() {
    }

    // @extra-start id=0
    @SuppressWarnings("unused")
    private void _i0() {
        try {
            new EventWatchBuilder((com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher) null);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=0

    // @extra-start id=1
    @SuppressWarnings("unused")
    private void _i1() {
        try {
            new EventWatchBuilder((com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher) null, EventWatchBuilder.PatternType.WILDCARD);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=1

    // @extra-start id=2
    @SuppressWarnings("unused")
    private void _i2() {
        try {
            EventWatchBuilder v = new EventWatchBuilder((com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher) null);
            v.onAnyClass();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=2

    // @extra-start id=3
    @SuppressWarnings("unused")
    private void _i3() {
        try {
            EventWatchBuilder v = new EventWatchBuilder((com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher) null);
            v.onClass(Object.class);
        } catch (Throwable t) {
        }
    }
    // @extra-end id=3

    // @extra-start id=4
    @SuppressWarnings("unused")
    private void _i4() {
        try {
            EventWatchBuilder v = new EventWatchBuilder((com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher) null);
            v.onClass("");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=4

    // @extra-start id=5
    @SuppressWarnings("unused")
    private void _i5() {
        try {
            EventWatchBuilder.PatternType.values();
        } catch (Throwable t) {
        }
    }
    // @extra-end id=5

    // @extra-start id=6
    @SuppressWarnings("unused")
    private void _i6() {
        try {
            EventWatchBuilder.PatternType.valueOf("WILDCARD");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=6

    // @extra-start id=7
    @SuppressWarnings("unused")
    private void _i7() {
        try {
            EventWatchBuilder.PatternType.valueOf("REGEX");
        } catch (Throwable t) {
        }
    }
    // @extra-end id=7















































}
