package dev.failsafe;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.concurrent.atomic.AtomicBoolean;
import java.util.concurrent.atomic.AtomicReference;
import org.junit.Test;

/**
 * Smoke tests for the public API of {@link FailsafeExecutor}.
 */
public class FailsafeExecutorSmokeTest {

  private FailsafeExecutor<Object> newExecutor() {
    return new FailsafeExecutor<>(Collections.<Policy<Object>>emptyList());
  }

  @Test
  public void testGetPolicies() {
    List<Policy<Object>> policies = new ArrayList<>();
    FailsafeExecutor<Object> executor = new FailsafeExecutor<>(policies);
    assertSame(policies, executor.getPolicies());
  }

  @Test
  public void testGet() {
    FailsafeExecutor<Object> executor = newExecutor();
    Object result = executor.get(() -> 1);
    assertEquals(1, result);
  }

  @Test
  public void testRun() {
    FailsafeExecutor<Object> executor = newExecutor();
    AtomicBoolean ran = new AtomicBoolean();
    executor.run(() -> ran.set(true));
    assertTrue(ran.get());
  }

  @Test
  public void testOnSuccessListener() {
    FailsafeExecutor<Object> executor = newExecutor();
    AtomicBoolean successCalled = new AtomicBoolean();
    AtomicReference<Object> eventResult = new AtomicReference<>();
    executor.onSuccess(event -> {
      successCalled.set(true);
      eventResult.set(event.getResult());
    });
    Object result = executor.get(() -> 42);
    assertEquals(42, result);
    assertTrue(successCalled.get());
    assertEquals(42, eventResult.get());
  }

  @Test
  public void testCompose() {
    FailsafeExecutor<Object> executor = newExecutor();
    Timeout<Object> timeout = Timeout.of(Duration.ofMinutes(1));
    FailsafeExecutor<Object> composed = executor.compose(timeout);
    assertEquals(0, executor.getPolicies().size());
    assertEquals(1, composed.getPolicies().size());
    assertSame(timeout, composed.getPolicies().get(0));
    Object result = composed.get(() -> 7);
    assertEquals(7, result);
  }

  @Test
  public void testWithExecutor() {
    FailsafeExecutor<Object> executor = newExecutor();
    assertSame(executor, executor.with(Runnable::run));
    // A plain Executor cannot propagate results, so get() returns null
    assertNull(executor.get(() -> 1));
  }
}
