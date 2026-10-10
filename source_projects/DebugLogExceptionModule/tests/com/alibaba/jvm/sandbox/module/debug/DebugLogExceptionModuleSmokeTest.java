package com.alibaba.jvm.sandbox.module.debug;

import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.filter.ExtFilter;
import com.alibaba.jvm.sandbox.api.filter.Filter;
import com.alibaba.jvm.sandbox.api.listener.EventListener;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchCondition;
import com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher;
import org.junit.Test;

import java.lang.reflect.Field;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertArrayEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * DebugLogExceptionModule 冒烟测试。
 * loadCompleted() 依赖 @Resource 注入的私有字段 moduleEventWatcher(默认为 null),
 * 这里用反射注入一个记录型 ModuleEventWatcher, 再调用 loadCompleted(),
 * 断言 watcher 收到了 watch(...) 调用, 且构建出的过滤器与 "java.lang.Exception/<init>/BEFORE" 匹配。
 */
public class DebugLogExceptionModuleSmokeTest {

    /**
     * 记录型 ModuleEventWatcher: 记录 EventWatchBuilder 发起的 watch 调用参数。
     */
    static class RecordingWatcher implements ModuleEventWatcher {

        int watchCount = 0;
        EventWatchCondition condition;
        EventListener listener;
        Progress progress;
        Event.Type[] eventTypes;

        @Override
        public int watch(Filter filter, EventListener listener, Progress progress, Event.Type... eventType) {
            return 0;
        }

        @Override
        public int watch(Filter filter, EventListener listener, Event.Type... eventType) {
            return 0;
        }

        @Override
        public int watch(EventWatchCondition condition, EventListener listener, Progress progress, Event.Type... eventType) {
            watchCount++;
            this.condition = condition;
            this.listener = listener;
            this.progress = progress;
            this.eventTypes = eventType;
            return 0;
        }

        @Override
        public void delete(int watcherId, Progress progress) {
        }

        @Override
        public void delete(int watcherId) {
        }

        @Override
        public void watching(Filter filter, EventListener listener, Progress wProgress, WatchCallback watchCb, Progress dProgress, Event.Type... eventType) throws Throwable {
        }

        @Override
        public void watching(Filter filter, EventListener listener, WatchCallback watchCb, Event.Type... eventType) throws Throwable {
        }
    }

    /**
     * 反射注入 moduleEventWatcher 并返回注入后的模块实例。
     */
    private static DebugLogExceptionModule newModuleWithWatcher(final RecordingWatcher watcher) throws Exception {
        final DebugLogExceptionModule module = new DebugLogExceptionModule();
        final Field field = DebugLogExceptionModule.class.getDeclaredField("moduleEventWatcher");
        field.setAccessible(true);
        field.set(module, watcher);
        return module;
    }

    @Test
    public void loadCompleted_invokesWatchWithBeforeEventType() throws Exception {
        final RecordingWatcher watcher = new RecordingWatcher();
        newModuleWithWatcher(watcher).loadCompleted();

        assertEquals(1, watcher.watchCount);
        assertNotNull(watcher.condition);
        assertNotNull(watcher.listener);
        assertNull(watcher.progress);
        assertArrayEquals(new Event.Type[]{Event.Type.BEFORE}, watcher.eventTypes);
    }

    @Test
    public void loadCompleted_builtFilterMatchesExceptionConstructor() throws Exception {
        final RecordingWatcher watcher = new RecordingWatcher();
        newModuleWithWatcher(watcher).loadCompleted();

        final Filter[] filters = watcher.condition.getOrFilterArray();
        assertEquals(1, filters.length);

        // 类过滤器: java.lang.Exception 应匹配, 其他类不应匹配
        assertTrue(filters[0].doClassFilter(0,
                "java.lang.Exception", "java.lang.Throwable",
                new String[0], new String[0]));
        assertFalse(filters[0].doClassFilter(0,
                "java.util.ArrayList", "java.util.AbstractList",
                new String[0], new String[0]));

        // 方法过滤器: 构造函数 "<init>" 应匹配, 其他方法不应匹配
        assertTrue(filters[0].doMethodFilter(0, "<init>",
                new String[0], new String[0], new String[0]));
        assertFalse(filters[0].doMethodFilter(0, "toString",
                new String[0], new String[0], new String[0]));
    }

    @Test
    public void loadCompleted_builderIncludesBootstrap() throws Exception {
        final RecordingWatcher watcher = new RecordingWatcher();
        newModuleWithWatcher(watcher).loadCompleted();

        final Filter[] filters = watcher.condition.getOrFilterArray();
        assertTrue(filters[0] instanceof ExtFilter);
        assertTrue(((ExtFilter) filters[0]).isIncludeBootstrap());
    }

}
