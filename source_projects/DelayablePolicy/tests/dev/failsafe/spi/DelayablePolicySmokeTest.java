package dev.failsafe.spi;

import dev.failsafe.DelayablePolicyConfig;
import dev.failsafe.DelayablePolicyTestSupport;
import dev.failsafe.ExecutionContext;
import dev.failsafe.function.CheckedRunnable;
import dev.failsafe.function.ContextualSupplier;
import org.junit.Test;

import java.time.Duration;
import java.time.Instant;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNull;

/**
 * Smoke tests for the {@link DelayablePolicy} fragment (dev.failsafe.spi.DelayablePolicy).
 * {@code computeDelay} is exercised through an anonymous implementation backed by a real {@link DelayablePolicyConfig}.
 */
public class DelayablePolicySmokeTest {
  private DelayablePolicy<Object> policyWith(DelayablePolicyConfig<Object> config) {
    return new DelayablePolicy<Object>() {
      @Override
      public DelayablePolicyConfig<Object> getConfig() {
        return config;
      }

      @Override
      public PolicyExecutor<Object> toExecutor(int policyIndex) {
        return null;
      }
    };
  }

  private ExecutionContext<Object> context(Object result, Throwable exception) {
    return new ExecutionContext<Object>() {
      @Override
      public void onCancel(CheckedRunnable cancelCallback) {
      }

      @Override
      public Duration getElapsedTime() {
        return Duration.ZERO;
      }

      @Override
      public Duration getElapsedAttemptTime() {
        return Duration.ZERO;
      }

      @Override
      public int getAttemptCount() {
        return 1;
      }

      @Override
      public int getExecutionCount() {
        return 1;
      }

      @Override
      @SuppressWarnings("unchecked")
      public <T extends Throwable> T getLastException() {
        return (T) exception;
      }

      @Override
      public Object getLastResult() {
        return result;
      }

      @Override
      public Object getLastResult(Object defaultValue) {
        return result != null ? result : defaultValue;
      }

      @Override
      public Instant getStartTime() {
        return Instant.EPOCH;
      }

      @Override
      public boolean isCancelled() {
        return false;
      }

      @Override
      public boolean isFirstAttempt() {
        return false;
      }

      @Override
      public boolean isRetry() {
        return true;
      }
    };
  }

  @Test
  public void noDelayFn_returnsNull() {
    DelayablePolicy<Object> policy = policyWith(DelayablePolicyTestSupport.newConfig());
    assertNull(policy.computeDelay(context("result", null)));
  }

  @Test
  public void delayFn_twoSeconds_returnsTwoSeconds() {
    ContextualSupplier<Object, Duration> delayFn = ctx -> Duration.ofSeconds(2);
    DelayablePolicy<Object> policy = policyWith(DelayablePolicyTestSupport.configWithDelayFn(delayFn));
    assertEquals(Duration.ofSeconds(2), policy.computeDelay(context("result", null)));
  }

  @Test
  public void delayFn_negative_returnsNull() {
    ContextualSupplier<Object, Duration> delayFn = ctx -> Duration.ofSeconds(-1);
    DelayablePolicy<Object> policy = policyWith(DelayablePolicyTestSupport.configWithDelayFn(delayFn));
    assertNull(policy.computeDelay(context("result", null)));
  }

  @Test
  public void nullContext_returnsNull() {
    ContextualSupplier<Object, Duration> delayFn = ctx -> Duration.ofSeconds(2);
    DelayablePolicy<Object> policy = policyWith(DelayablePolicyTestSupport.configWithDelayFn(delayFn));
    assertNull(policy.computeDelay(null));
  }
}
