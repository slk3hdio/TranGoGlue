package dev.failsafe;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import java.time.Duration;
import java.util.Collections;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.TimeUnit;
import org.junit.Test;

/**
 * TimeoutExecutor 的附加集成测试，通过 FailsafeExecutor 覆盖同步和异步包装路径。
 */
public class TimeoutExecutorAdditionalTest {

  /**
   * 创建带指定超时策略的执行器。
   *
   * @param duration 最大执行时长
   * @return 配置超时策略的执行器
   */
  private FailsafeExecutor<Object> newExecutor(Duration duration) {
    Timeout<Object> timeout = Timeout.of(duration);
    return new FailsafeExecutor<>(Collections.<Policy<Object>>singletonList(timeout));
  }

  /**
   * 验证同步快速任务在超时前正常返回。
   */
  @Test
  public void synchronousExecutionCompletesBeforeTimeout() {
    assertEquals(Integer.valueOf(41), newExecutor(Duration.ofSeconds(1)).get(() -> 41));
  }

  /**
   * 验证同步慢任务被超时策略中断。
   */
  @Test
  public void synchronousExecutionTimesOut() {
    try {
      newExecutor(Duration.ofMillis(20)).get(() -> {
        Thread.sleep(200);
        return 42;
      });
      fail("慢任务应触发同步超时");
    } catch (TimeoutExceededException expected) {
      assertNotNull(expected);
    }
  }

  /**
   * 验证异步快速任务在超时前正常完成。
   *
   * @throws Exception 异步任务未能正常完成时抛出
   */
  @Test
  public void asynchronousExecutionCompletesBeforeTimeout() throws Exception {
    assertEquals(Integer.valueOf(43), newExecutor(Duration.ofSeconds(1)).getAsync(() -> 43)
      .get(5, TimeUnit.SECONDS));
  }

  /**
   * 验证异步慢任务以 TimeoutExceededException 失败。
   *
   * @throws Exception 等待异步任务失败时发生非预期错误则抛出
   */
  @Test
  public void asynchronousExecutionTimesOut() throws Exception {
    try {
      newExecutor(Duration.ofMillis(20)).getAsync(() -> {
        Thread.sleep(200);
        return 44;
      }).get(5, TimeUnit.SECONDS);
      fail("慢任务应触发异步超时");
    } catch (ExecutionException expected) {
      assertTrue(expected.getCause() instanceof TimeoutExceededException);
    }
  }

  /**
   * 验证取消异步执行会传播到超时任务并取消等待中的工作。
   *
   * @throws Exception 等待任务启动失败时抛出
   */
  @Test
  public void asynchronousCancellationPropagatesToTimeoutTask() throws Exception {
    CountDownLatch started = new CountDownLatch(1);
    CountDownLatch release = new CountDownLatch(1);
    CompletableFuture<Object> future = newExecutor(Duration.ofSeconds(5)).getAsync(() -> {
      started.countDown();
      release.await(5, TimeUnit.SECONDS);
      return 45;
    });

    assertTrue(started.await(5, TimeUnit.SECONDS));
    assertTrue(future.cancel(true));
    release.countDown();
    assertTrue(future.isCancelled());
  }
}
