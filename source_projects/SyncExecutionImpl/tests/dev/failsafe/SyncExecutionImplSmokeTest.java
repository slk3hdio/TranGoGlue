package dev.failsafe;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

import java.util.Collections;
import org.junit.Test;

/**
 * Smoke tests for the public API of {@link SyncExecutionImpl}.
 */
public class SyncExecutionImplSmokeTest {

  private SyncExecutionImpl<Object> newExecution() {
    return new SyncExecutionImpl<>(Collections.<Policy<Object>>emptyList());
  }

  @Test
  public void testInitialState() {
    SyncExecutionImpl<Object> execution = newExecution();
    assertTrue(execution.isPreExecuted());
    assertFalse(execution.isComplete());
    assertFalse(execution.isInterrupted());
    assertFalse(execution.isCancelled());
    assertTrue(execution.getDelay().isZero());
  }

  @Test
  public void testRecordResult() {
    SyncExecutionImpl<Object> execution = newExecution();
    execution.recordResult("foo");
    assertEquals("foo", execution.getResult().getResult());
    assertEquals("foo", execution.getLastResult());
    assertTrue(execution.isComplete());
    assertEquals(1, execution.getAttemptCount());
    assertEquals(1, execution.getExecutionCount());
  }

  @Test
  public void testRecordException() {
    SyncExecutionImpl<Object> execution = newExecution();
    IllegalStateException boom = new IllegalStateException("boom");
    execution.recordException(boom);
    assertSame(boom, execution.getResult().getException());
    assertTrue(execution.getLastException() instanceof IllegalStateException);
    assertTrue(execution.isComplete());
  }

  @Test
  public void testComplete() {
    SyncExecutionImpl<Object> execution = newExecution();
    execution.complete();
    assertTrue(execution.isComplete());
    assertTrue(execution.getResult().isNonResult());
  }

  @Test
  public void testInterrupt() {
    SyncExecutionImpl<Object> execution = newExecution();
    execution.setInterruptable(true);
    execution.interrupt();
    assertTrue(execution.isInterrupted());
    // Clear the interrupt flag that interrupt() set on the current thread
    Thread.interrupted();

    SyncExecutionImpl<Object> uninterruptable = newExecution();
    uninterruptable.setInterruptable(false);
    uninterruptable.interrupt();
    assertFalse(uninterruptable.isInterrupted());
  }

  @Test
  public void testCancelAndCopy() {
    SyncExecutionImpl<Object> execution = newExecution();
    assertSame(execution, execution.copy());
    assertTrue(execution.cancel());
    assertTrue(execution.isCancelled());
    assertFalse(execution.cancel());
  }
}
