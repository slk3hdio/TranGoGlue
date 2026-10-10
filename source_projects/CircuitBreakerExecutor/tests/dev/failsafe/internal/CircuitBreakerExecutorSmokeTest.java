package dev.failsafe.internal;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertTrue;

import dev.failsafe.CircuitBreaker;
import dev.failsafe.spi.ExecutionResult;
import java.time.Duration;
import org.junit.Test;

/**
 * Smoke tests for the public API of {@link CircuitBreakerExecutor}.
 */
public class CircuitBreakerExecutorSmokeTest {

  @SuppressWarnings("unchecked")
  private CircuitBreakerImpl<Object> newCircuitBreaker() {
    return (CircuitBreakerImpl<Object>) CircuitBreaker.ofDefaults();
  }

  @SuppressWarnings("unchecked")
  private CircuitBreakerImpl<Object> newCircuitBreakerWithFailureThreshold(int threshold) {
    return (CircuitBreakerImpl<Object>) CircuitBreaker.builder().withFailureThreshold(threshold).build();
  }

  @Test
  public void testConstructor() {
    CircuitBreakerImpl<Object> circuitBreaker = newCircuitBreaker();
    assertTrue(circuitBreaker.isClosed());
    assertEquals(0, new CircuitBreakerExecutor<>(circuitBreaker, 0).getPolicyIndex());
    assertEquals(1, new CircuitBreakerExecutor<>(circuitBreaker, 1).getPolicyIndex());
  }

  @Test
  public void testOnSuccessRecordsSuccess() {
    CircuitBreakerImpl<Object> circuitBreaker = newCircuitBreaker();
    CircuitBreakerExecutor<Object> executor = new CircuitBreakerExecutor<>(circuitBreaker, 0);
    executor.onSuccess(ExecutionResult.success("ok"));
    assertEquals(1, circuitBreaker.getSuccessCount());
    assertEquals(1, circuitBreaker.getExecutionCount());
    assertTrue(circuitBreaker.isClosed());
  }

  @Test
  public void testOnSuccessRecordsMultipleSuccesses() {
    // A threshold > 1 enables rolling (counting) stats, so successes accumulate
    CircuitBreakerImpl<Object> circuitBreaker = newCircuitBreakerWithFailureThreshold(3);
    CircuitBreakerExecutor<Object> executor = new CircuitBreakerExecutor<>(circuitBreaker, 0);
    executor.onSuccess(ExecutionResult.success("a"));
    executor.onSuccess(ExecutionResult.success("b"));
    executor.onSuccess(ExecutionResult.success("c"));
    assertEquals(3, circuitBreaker.getSuccessCount());
    assertEquals(3, circuitBreaker.getExecutionCount());
  }

  @Test
  public void testDefaultConfig() {
    CircuitBreakerImpl<Object> circuitBreaker = newCircuitBreaker();
    assertEquals(1, circuitBreaker.getConfig().getFailureThreshold());
    assertEquals(1, circuitBreaker.getConfig().getFailureThresholdingCapacity());
    assertEquals(Duration.ofMinutes(1), circuitBreaker.getConfig().getDelay());
    assertEquals(0, circuitBreaker.getConfig().getFailureRateThreshold());
  }
}
