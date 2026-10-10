package dev.failsafe;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotSame;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;
import static org.junit.Assert.fail;

import dev.failsafe.function.ContextualSupplier;
import dev.failsafe.spi.ExecutionResult;
import dev.failsafe.spi.Scheduler;
import java.util.Collections;
import org.junit.Test;

/**
 * SyncExecutionImpl 的附加行为测试，覆盖组合记录和非独立执行路径。
 */
public class SyncExecutionImplAdditionalTest {

  /**
   * 验证 record 同时接收结果和异常时会完整保存异常状态。
   */
  @Test
  public void recordStoresCombinedResult() {
    SyncExecutionImpl<Object> execution = new SyncExecutionImpl<>(Collections.<Policy<Object>>emptyList());
    IllegalArgumentException expected = new IllegalArgumentException("boom");

    execution.record("partial", expected);

    assertEquals("partial", execution.getResult().getResult());
    assertSame(expected, execution.getResult().getException());
    assertTrue(execution.isComplete());
  }

  /**
   * 验证通过 FailsafeExecutor 创建的非独立执行能够返回结果。
   */
  @Test
  public void executeSyncReturnsSupplierResult() {
    FailsafeExecutor<Object> executor = new FailsafeExecutor<>(Collections.<Policy<Object>>emptyList());
    assertEquals(Integer.valueOf(31), executor.get(() -> 31));
  }

  /**
   * 验证可复用调用会复制执行状态并再次运行供应器。
   */
  @Test
  public void callExecutesMoreThanOnce() {
    FailsafeExecutor<Object> executor = new FailsafeExecutor<>(Collections.<Policy<Object>>emptyList());
    ContextualSupplier<Object, Object> supplier = context -> context.getAttemptCount();
    Call<Object> call = executor.newCall(supplier);

    assertEquals(Integer.valueOf(0), call.execute());
    assertEquals(Integer.valueOf(1), call.execute());
  }

  /**
   * 验证非独立执行的 copy 会创建共享跨尝试状态的新实例。
   */
  @Test
  public void copyCreatesNewInstanceForExecutorBackedExecution() {
    FailsafeExecutor<Object> executor = new FailsafeExecutor<>(Collections.<Policy<Object>>emptyList());
    SyncExecutionImpl<Object> execution = new SyncExecutionImpl<>(executor, Scheduler.DEFAULT, null,
      ignored -> ExecutionResult.success(32));

    assertNotSame(execution, execution.copy());
  }

  /**
   * 验证同步执行保留运行时异常对象。
   */
  @Test
  public void executeSyncRethrowsRuntimeException() {
    FailsafeExecutor<Object> executor = new FailsafeExecutor<>(Collections.<Policy<Object>>emptyList());
    IllegalStateException expected = new IllegalStateException("boom");

    try {
      executor.get(() -> {
        throw expected;
      });
      fail("应重新抛出运行时异常");
    } catch (IllegalStateException actual) {
      assertSame(expected, actual);
    }
  }
}
