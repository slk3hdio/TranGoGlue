// 针对性补充测试(手工编写): 覆盖 FailsafeExecutor 合并基线未触及的
// newCall/getAsync*/getStageAsync*/runAsync*/onComplete/onFailure 等核心 public 方法。
// 与 tests/、additional_tests/ 及自动生成的 ExtraTest 批次相互隔离。
package dev.failsafe;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import dev.failsafe.function.AsyncRunnable;
import dev.failsafe.function.ContextualRunnable;
import dev.failsafe.function.ContextualSupplier;
import java.util.Collections;
import java.util.concurrent.CompletableFuture;
import java.util.concurrent.CompletionStage;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.Test;

/**
 * FailsafeExecutor 核心 public 方法的针对性补充测试。
 * 测试类与模块同包(dev.failsafe), 以便使用包级私有的列表构造器。
 * 所有异步调用均以 get(timeout) 收尾, 避免用例悬挂。
 */
public class FailsafeExecutorCoreExtraTest {

  /** 创建零策略执行器, 供各用例复用。 */
  private FailsafeExecutor<Object> newExecutor() {
    return new FailsafeExecutor<>(Collections.<Policy<Object>>emptyList());
  }

  /** 覆盖 newCall(ContextualRunnable): 执行后回调标志位应被置位。 */
  @Test
  public void testNewCallWithRunnable() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    final AtomicBoolean ran = new AtomicBoolean();
    Call<Void> call = executor.newCall((ContextualRunnable<Void>) ctx -> ran.set(true));
    call.execute();
    assertTrue("newCall 应真正执行 runnable", ran.get());
  }

  /** 覆盖 newCall(ContextualSupplier): execute 应返回 supplier 的结果。 */
  @Test
  public void testNewCallWithSupplier() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    Call<Integer> call = executor.newCall((ContextualSupplier<Integer, Integer>) ctx -> 5);
    assertEquals(Integer.valueOf(5), call.execute());
  }

  /** 覆盖 getAsync(CheckedSupplier): 异步返回 supplier 结果。 */
  @Test
  public void testGetAsyncWithCheckedSupplier() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    CompletableFuture<Integer> future = executor.getAsync(() -> 7);
    assertEquals(Integer.valueOf(7), future.get(10, TimeUnit.SECONDS));
  }

  /** 覆盖 getAsync(ContextualSupplier): 异步返回上下文 supplier 结果。 */
  @Test
  public void testGetAsyncWithContextualSupplier() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    CompletableFuture<Integer> future =
        executor.getAsync((ContextualSupplier<Integer, Integer>) ctx -> 8);
    assertEquals(Integer.valueOf(8), future.get(10, TimeUnit.SECONDS));
  }

  /** 覆盖 getAsyncExecution(AsyncRunnable): 手动 record 结果后 future 应完成。 */
  @Test
  public void testGetAsyncExecution() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    CompletableFuture<Integer> future =
        executor.getAsyncExecution((AsyncRunnable<Integer>) execution ->
            execution.recordResult(11));
    assertEquals(Integer.valueOf(11), future.get(10, TimeUnit.SECONDS));
  }

  /** 覆盖 getStageAsync(CheckedSupplier): 完成态 stage 的值应被透传。 */
  @Test
  public void testGetStageAsyncWithCheckedSupplier() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    CompletableFuture<Integer> future =
        executor.getStageAsync(() -> CompletableFuture.completedFuture(9));
    assertEquals(Integer.valueOf(9), future.get(10, TimeUnit.SECONDS));
  }

  /** 覆盖 getStageAsync(ContextualSupplier): 上下文版本的 stage 透传。 */
  @Test
  public void testGetStageAsyncWithContextualSupplier() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    CompletableFuture<Integer> future = executor.getStageAsync(
        (ContextualSupplier<Integer, CompletionStage<Integer>>) ctx ->
            CompletableFuture.completedFuture(10));
    assertEquals(Integer.valueOf(10), future.get(10, TimeUnit.SECONDS));
  }

  /** 覆盖 runAsync(CheckedRunnable): 异步执行后标志位应被置位。 */
  @Test
  public void testRunAsyncWithCheckedRunnable() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    final AtomicBoolean ran = new AtomicBoolean();
    executor.runAsync(() -> ran.set(true)).get(10, TimeUnit.SECONDS);
    assertTrue("runAsync 应真正执行 runnable", ran.get());
  }

  /** 覆盖 runAsync(ContextualRunnable): 上下文版本异步执行。 */
  @Test
  public void testRunAsyncWithContextualRunnable() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    final AtomicBoolean ran = new AtomicBoolean();
    CompletableFuture<Void> future =
        executor.runAsync((ContextualRunnable<Void>) ctx -> ran.set(true));
    future.get(10, TimeUnit.SECONDS);
    assertTrue("runAsync 应真正执行 runnable", ran.get());
  }

  /** 覆盖 runAsyncExecution(AsyncRunnable): record(null) 后 future 以 null 完成。 */
  @Test
  public void testRunAsyncExecution() throws Exception {
    FailsafeExecutor<Object> executor = newExecutor();
    CompletableFuture<Void> future =
        executor.runAsyncExecution((AsyncRunnable<Void>) execution ->
            execution.recordResult(null));
    assertNull(future.get(10, TimeUnit.SECONDS));
  }

  /** 覆盖 onComplete(EventListener): 执行完成后监听器应被回调。 */
  @Test
  public void testOnCompleteFires() {
    FailsafeExecutor<Object> executor = newExecutor();
    final AtomicBoolean fired = new AtomicBoolean();
    executor.onComplete(event -> fired.set(true));
    executor.get(() -> 1);
    assertTrue("onComplete 监听器应被回调", fired.get());
  }

  /** 覆盖 onFailure(EventListener): 执行失败时监听器应被回调, 异常向上透传。 */
  @Test
  public void testOnFailureFires() {
    FailsafeExecutor<Object> executor = newExecutor();
    final AtomicBoolean fired = new AtomicBoolean();
    executor.onFailure(event -> fired.set(true));
    try {
      executor.get(() -> {
        throw new IllegalStateException("boom");
      });
      fail("执行失败应抛出异常");
    } catch (IllegalStateException expected) {
      // 零策略下 RuntimeException 直接透传
    }
    assertTrue("onFailure 监听器应被回调", fired.get());
  }
}
