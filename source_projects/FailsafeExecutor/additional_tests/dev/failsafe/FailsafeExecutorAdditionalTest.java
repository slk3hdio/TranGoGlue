package dev.failsafe;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import dev.failsafe.function.ContextualSupplier;
import dev.failsafe.function.ContextualRunnable;
import dev.failsafe.spi.Scheduler;
import java.util.Collections;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;

/**
 * FailsafeExecutor 的附加行为测试，覆盖上下文、异步调用、监听器和执行器配置。
 */
public class FailsafeExecutorAdditionalTest {

  /**
   * 创建不附加失败策略的执行器。
   *
   * @return 可直接执行任务的 Failsafe 执行器
   */
  private FailsafeExecutor<Object> newExecutor() {
    return new FailsafeExecutor<>(Collections.<Policy<Object>>emptyList());
  }

  /**
   * 验证上下文供应器、上下文任务和可复用调用对象。
   */
  @Test
  public void executesContextualAndCallApis() {
    FailsafeExecutor<Object> executor = newExecutor();
    AtomicBoolean ran = new AtomicBoolean();

    ContextualSupplier<Object, Object> supplier = context -> {
      assertTrue(context.isFirstAttempt());
      return 11;
    };
    assertEquals(Integer.valueOf(11), executor.get(supplier));
    assertEquals(Integer.valueOf(12), executor.newCall((ContextualSupplier<Object, Object>) context -> 12)
      .execute());
    executor.run(context -> ran.set(context.isFirstAttempt()));

    assertTrue(ran.get());
  }

  /**
   * 验证上下文任务形式的可复用调用可以执行副作用。
   */
  @Test
  public void executesContextualRunnableCall() {
    AtomicBoolean ran = new AtomicBoolean();
    Call<Void> call = newExecutor().newCall((ContextualRunnable<Void>) context -> ran.set(true));

    call.execute();

    assertTrue(ran.get());
  }

  /**
   * 验证异步供应器、阶段供应器和手动记录执行结果的路径。
   *
   * @throws Exception 异步结果未能正常完成时抛出
   */
  @Test
  public void executesAsyncResultApis() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();

    assertEquals(Integer.valueOf(21), executor.getAsync(() -> 21).get(5, TimeUnit.SECONDS));
    assertEquals(Integer.valueOf(22), executor.getAsync(context -> 22).get(5, TimeUnit.SECONDS));
    assertEquals(Integer.valueOf(23), executor.getAsyncExecution(execution -> execution.recordResult(23))
      .get(5, TimeUnit.SECONDS));
    assertEquals(Integer.valueOf(24), executor.getStageAsync(() -> CompletableFuture.completedFuture(24))
      .get(5, TimeUnit.SECONDS));
    assertEquals(Integer.valueOf(25), executor.getStageAsync(context -> CompletableFuture.completedFuture(25))
      .get(5, TimeUnit.SECONDS));
  }

  /**
   * 验证三种异步任务入口都能完成并产生副作用。
   *
   * @throws Exception 异步任务未能正常完成时抛出
   */
  @Test
  public void executesAsyncRunnableApis() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    AtomicInteger count = new AtomicInteger();

    executor.runAsync(() -> count.incrementAndGet()).get(5, TimeUnit.SECONDS);
    executor.runAsync(context -> count.incrementAndGet()).get(5, TimeUnit.SECONDS);
    executor.runAsyncExecution(execution -> {
      count.incrementAndGet();
      execution.complete();
    }).get(5, TimeUnit.SECONDS);

    assertEquals(3, count.get());
  }

  /**
   * 验证完成与失败监听器接收正确的执行结果。
   */
  @Test
  public void notifiesCompletionAndFailureListeners() {
    FailsafeExecutor<Object> executor = newExecutor();
    AtomicInteger completeCount = new AtomicInteger();
    AtomicReference<Throwable> failure = new AtomicReference<>();
    executor.onComplete(event -> completeCount.incrementAndGet());
    executor.onFailure(event -> failure.set(event.getException()));

    IllegalStateException expected = new IllegalStateException("boom");
    try {
      executor.get(() -> {
        throw expected;
      });
      fail("应重新抛出运行时异常");
    } catch (IllegalStateException actual) {
      assertSame(expected, actual);
    }

    assertEquals(1, completeCount.get());
    assertSame(expected, failure.get());
  }

  /**
   * 验证调度线程池、普通线程池和自定义调度器的配置重载。
   */
  @Test
  public void acceptsAllExecutorConfigurationOverloads() {
    ScheduledExecutorService scheduled = Executors.newScheduledThreadPool(2);
    ExecutorService executorService = Executors.newFixedThreadPool(2);
    try {
      FailsafeExecutor<Object> executor = newExecutor();
      assertSame(executor, executor.with(scheduled));
      assertSame(executor, executor.with(executorService));
      assertSame(executor, executor.with(Scheduler.DEFAULT));
    } finally {
      scheduled.shutdownNow();
      executorService.shutdownNow();
    }
  }
}
