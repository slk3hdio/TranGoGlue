package dev.failsafe.internal;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

import dev.failsafe.CircuitBreaker;
import dev.failsafe.CircuitBreakerOpenException;
import dev.failsafe.spi.ExecutionResult;
import org.junit.Test;

/**
 * CircuitBreakerExecutor 的附加行为测试，覆盖执行前拦截与失败记录路径。
 */
public class CircuitBreakerExecutorAdditionalTest {

  /**
   * 创建指定失败阈值的断路器实现。
   *
   * @param threshold 触发断路的失败次数
   * @return 可供执行器直接使用的断路器实现
   */
  @SuppressWarnings("unchecked")
  private CircuitBreakerImpl<Object> newCircuitBreaker(int threshold) {
    return (CircuitBreakerImpl<Object>) CircuitBreaker.builder()
      .withFailureThreshold(threshold)
      .build();
  }

  /**
   * 验证关闭状态允许执行，而打开状态返回断路异常。
   */
  @Test
  public void preExecuteReflectsCircuitState() {
    CircuitBreakerImpl<Object> breaker = newCircuitBreaker(2);
    CircuitBreakerExecutor<Object> executor = new CircuitBreakerExecutor<>(breaker, 0);

    assertNull(executor.preExecute());
    breaker.open();

    ExecutionResult<Object> result = executor.preExecute();
    assertTrue(result.getException() instanceof CircuitBreakerOpenException);
  }

  /**
   * 验证失败结果会原样返回并计入断路器统计。
   */
  @Test
  public void onFailureRecordsAndReturnsOriginalResult() {
    CircuitBreakerImpl<Object> breaker = newCircuitBreaker(2);
    CircuitBreakerExecutor<Object> executor = new CircuitBreakerExecutor<>(breaker, 0);
    ExecutionResult<Object> failure = ExecutionResult.exception(new IllegalStateException("boom"));

    assertSame(failure, executor.onFailure(null, failure));
    assertEquals(1, breaker.getFailureCount());
    assertEquals(1, breaker.getExecutionCount());
  }
}
