package dev.failsafe.internal;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import dev.failsafe.Timeout;
import dev.failsafe.TimeoutExceededException;
import dev.failsafe.spi.ExecutionResult;
import java.time.Duration;
import org.junit.Test;

/**
 * Smoke tests for the public API of {@link TimeoutExecutor}.
 */
public class TimeoutExecutorSmokeTest {

  @SuppressWarnings("unchecked")
  private TimeoutImpl<Object> newTimeout() {
    return (TimeoutImpl<Object>) Timeout.of(Duration.ofMinutes(1));
  }

  @Test
  public void testConstructor() {
    assertEquals(0, new TimeoutExecutor<>(newTimeout(), 0).getPolicyIndex());
    assertEquals(2, new TimeoutExecutor<>(newTimeout(), 2).getPolicyIndex());
  }

  @Test
  public void testIsFailureOnTimeoutExceeded() {
    TimeoutExecutor<Object> executor = new TimeoutExecutor<>(newTimeout(), 0);
    assertTrue(executor.isFailure(ExecutionResult.exception(new TimeoutExceededException(newTimeout()))));
  }

  @Test
  public void testIsFailureOnSuccess() {
    TimeoutExecutor<Object> executor = new TimeoutExecutor<>(newTimeout(), 0);
    assertFalse(executor.isFailure(ExecutionResult.success("ok")));
    assertFalse(executor.isFailure(new ExecutionResult<>("ok", null)));
  }

  @Test
  public void testIsFailureOnNonResultAndOtherException() {
    TimeoutExecutor<Object> executor = new TimeoutExecutor<>(newTimeout(), 0);
    assertFalse(executor.isFailure(ExecutionResult.none()));
    assertFalse(executor.isFailure(ExecutionResult.exception(new IllegalStateException("boom"))));
  }
}
