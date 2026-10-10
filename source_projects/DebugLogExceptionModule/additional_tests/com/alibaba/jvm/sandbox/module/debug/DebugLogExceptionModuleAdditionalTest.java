package com.alibaba.jvm.sandbox.module.debug;

import static org.junit.Assert.assertNotNull;

import com.alibaba.jvm.sandbox.api.event.BeforeEvent;
import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.filter.Filter;
import com.alibaba.jvm.sandbox.api.listener.EventListener;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchCondition;
import com.alibaba.jvm.sandbox.api.resource.ModuleEventWatcher;
import java.lang.reflect.Field;
import org.junit.Test;

/**
 * DebugLogExceptionModule 的附加测试，实际触发 loadCompleted 注册的事件监听器。
 */
public class DebugLogExceptionModuleAdditionalTest {

  /**
   * 只记录扩展条件监听器的观察器，用于隔离模块注册行为。
   */
  private static class RecordingWatcher implements ModuleEventWatcher {
    private EventListener listener;

    /** {@inheritDoc} */
    @Override
    public int watch(Filter filter, EventListener eventListener, Progress progress, Event.Type... eventTypes) {
      return 0;
    }

    /** {@inheritDoc} */
    @Override
    public int watch(Filter filter, EventListener eventListener, Event.Type... eventTypes) {
      return 0;
    }

    /** {@inheritDoc} */
    @Override
    public int watch(EventWatchCondition condition, EventListener eventListener, Progress progress,
      Event.Type... eventTypes) {
      listener = eventListener;
      return 1;
    }

    /** {@inheritDoc} */
    @Override
    public void delete(int watcherId, Progress progress) {
    }

    /** {@inheritDoc} */
    @Override
    public void delete(int watcherId) {
    }

    /** {@inheritDoc} */
    @Override
    public void watching(Filter filter, EventListener eventListener, Progress watchProgress,
      WatchCallback callback, Progress deleteProgress, Event.Type... eventTypes) {
    }

    /** {@inheritDoc} */
    @Override
    public void watching(Filter filter, EventListener eventListener, WatchCallback callback,
      Event.Type... eventTypes) {
    }
  }

  /**
   * 创建注入记录观察器的模块。
   *
   * @param watcher 用于接收模块注册结果的观察器
   * @return 已完成依赖注入的模块
   * @throws Exception 反射字段访问失败时抛出
   */
  private DebugLogExceptionModule newModule(RecordingWatcher watcher) throws Exception {
    DebugLogExceptionModule module = new DebugLogExceptionModule();
    Field field = DebugLogExceptionModule.class.getDeclaredField("moduleEventWatcher");
    field.setAccessible(true);
    field.set(module, watcher);
    return module;
  }

  /**
   * 验证注册的监听器可处理异常构造事件且不会抛出异常。
   *
   * @throws Throwable 事件监听失败时抛出
   */
  @Test
  public void registeredListenerHandlesBeforeEvent() throws Throwable {
    RecordingWatcher watcher = new RecordingWatcher();
    newModule(watcher).loadCompleted();
    assertNotNull(watcher.listener);

    IllegalStateException target = new IllegalStateException("additional-test");
    BeforeEvent event = new BeforeEvent(1, 1, getClass().getClassLoader(),
      IllegalStateException.class.getName(), "<init>", "(Ljava/lang/String;)V", target,
      new Object[] { "additional-test" });
    watcher.listener.onEvent(event);
  }
}
