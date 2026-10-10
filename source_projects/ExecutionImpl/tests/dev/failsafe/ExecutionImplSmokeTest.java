package dev.failsafe;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

import dev.failsafe.spi.ExecutionResult;
import java.util.Collections;
import java.util.concurrent.atomic.AtomicBoolean;
import org.junit.Test;

/**
 * Smoke tests for the public API of {@link ExecutionImpl}.
 */
public class ExecutionImplSmokeTest {

  private ExecutionImpl<Object> newExecution() {
    return new ExecutionImpl<>(Collections.<Policy<Object>>emptyList());
  }

  @Test
  public void testRecordAttempt() {
    ExecutionImpl<Object> execution = newExecution();
    assertEquals(0, execution.getAttemptCount());
    execution.recordAttempt();
    assertEquals(1, execution.getAttemptCount());
    assertTrue(execution.isFirstAttempt());
    assertFalse(execution.isRetry());
  }

  @Test
  public void testRecordResult() {
    ExecutionImpl<Object> execution = newExecution();
    execution.preExecute();
    assertTrue(execution.isPreExecuted());
    execution.record(ExecutionResult.success("foo"));
    assertEquals("foo", execution.getResult().getResult());
    assertEquals("foo", execution.getLastResult());
    assertEquals(1, execution.getExecutionCount());
    assertEquals(1, execution.getAttemptCount());
  }

  @Test
  public void testRecordException() {
    ExecutionImpl<Object> execution = newExecution();
    execution.preExecute();
    IllegalStateException boom = new IllegalStateException("boom");
    execution.record(ExecutionResult.exception(boom));
    assertSame(boom, execution.getResult().getException());
    assertTrue(execution.getLastException() instanceof IllegalStateException);
  }

  @Test
  public void testCancelAndCallback() {
    ExecutionImpl<Object> execution = newExecution();
    AtomicBoolean callbackCalled = new AtomicBoolean();
    execution.onCancel(() -> callbackCalled.set(true));
    assertFalse(execution.isCancelled());
    assertTrue(execution.cancel());
    assertTrue(execution.isCancelled());
    assertTrue(callbackCalled.get());
    assertFalse(execution.cancel());
  }

  @Test
  public void testLatestLockAndPreviousResult() {
    ExecutionImpl<Object> execution = newExecution();
    assertNotNull(execution.getLock());
    assertSame(execution, execution.getLatest());
    assertEquals("default", execution.getLastResult("default"));

    execution.preExecute();
    execution.record(ExecutionResult.success("foo"));
    ExecutionImpl<Object> attempt = new ExecutionImpl<>(execution);
    assertSame(attempt, execution.getLatest());
    assertSame(attempt, attempt.getLatest());
    assertEquals("foo", attempt.getLastResult());
    assertSame(execution.getLock(), attempt.getLock());
  }

  @Test
  public void testTimingAndToString() {
    ExecutionImpl<Object> execution = newExecution();
    assertFalse(execution.getElapsedTime().isNegative());
    assertFalse(execution.getElapsedAttemptTime().isNegative());
    execution.preExecute();
    assertNotNull(execution.getStartTime());
    assertTrue(execution.toString().contains("attempts="));
  }
}
