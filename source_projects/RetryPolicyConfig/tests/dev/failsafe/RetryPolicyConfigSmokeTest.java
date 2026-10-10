package dev.failsafe;

import dev.failsafe.event.EventListener;
import dev.failsafe.event.ExecutionCompletedEvent;
import org.junit.Test;

import java.time.Duration;
import java.util.ArrayList;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertTrue;

/**
 * Smoke tests for the {@link RetryPolicyConfig} fragment (dev.failsafe.RetryPolicyConfig).
 * The constructor is package-private, so this test lives in the same package and drives getter changes through the
 * package-private fields, since no builder is part of this fragment.
 */
public class RetryPolicyConfigSmokeTest {
  @Test
  public void defaults() {
    RetryPolicyConfig<Object> config = new RetryPolicyConfig<>();

    assertEquals(0, config.getMaxRetries());
    assertEquals(1, config.getMaxAttempts());
    assertFalse(config.allowsRetries());
    assertNull(config.getDelay());
    assertNull(config.getDelayMin());
    assertNull(config.getDelayMax());
    assertEquals(0.0, config.getDelayFactor(), 0.0);
    assertNull(config.getMaxDelay());
    assertNull(config.getMaxDuration());
    assertNull(config.getJitter());
    assertEquals(0.0, config.getJitterFactor(), 0.0);
    assertNull(config.getAbortConditions());
    assertNull(config.getAbortListener());
    assertNull(config.getFailedAttemptListener());
    assertNull(config.getRetriesExceededListener());
    assertNull(config.getRetryListener());
    assertNull(config.getRetryScheduledListener());
  }

  @Test
  public void allowsRetries_dependsOnMaxRetries() {
    RetryPolicyConfig<Object> config = new RetryPolicyConfig<>();

    config.maxRetries = 3;
    assertTrue(config.allowsRetries());
    assertEquals(3, config.getMaxRetries());
    assertEquals(4, config.getMaxAttempts());

    // -1 means unlimited retries
    config.maxRetries = -1;
    assertTrue(config.allowsRetries());
    assertEquals(-1, config.getMaxRetries());
    assertEquals(-1, config.getMaxAttempts());

    // 0 retries -> no retries allowed
    config.maxRetries = 0;
    assertFalse(config.allowsRetries());
  }

  @Test
  public void allowsRetries_dependsOnMaxDuration() {
    RetryPolicyConfig<Object> config = new RetryPolicyConfig<>();
    config.maxRetries = 2;

    config.maxDuration = Duration.ofSeconds(1);
    assertTrue(config.allowsRetries());

    // A zero max duration disables retries
    config.maxDuration = Duration.ZERO;
    assertFalse(config.allowsRetries());
  }

  @Test
  public void delayAndJitterGetters_reflectConfiguredValues() {
    RetryPolicyConfig<Object> config = new RetryPolicyConfig<>();

    config.delay = Duration.ofSeconds(2);
    config.delayMin = Duration.ofMillis(100);
    config.delayMax = Duration.ofMillis(500);
    config.delayFactor = 1.5;
    config.maxDelay = Duration.ofSeconds(10);
    config.jitter = Duration.ofMillis(50);
    config.jitterFactor = 0.25;
    config.maxDuration = Duration.ofMinutes(1);

    assertEquals(Duration.ofSeconds(2), config.getDelay());
    assertEquals(Duration.ofMillis(100), config.getDelayMin());
    assertEquals(Duration.ofMillis(500), config.getDelayMax());
    assertEquals(1.5, config.getDelayFactor(), 0.0);
    assertEquals(Duration.ofSeconds(10), config.getMaxDelay());
    assertEquals(Duration.ofMillis(50), config.getJitter());
    assertEquals(0.25, config.getJitterFactor(), 0.0);
    assertEquals(Duration.ofMinutes(1), config.getMaxDuration());
  }

  @Test
  public void abortConditionsAndListeners_reflectConfiguredValues() {
    RetryPolicyConfig<Object> config = new RetryPolicyConfig<>();

    config.abortConditions = new ArrayList<>();
    assertNotNull(config.getAbortConditions());
    assertTrue(config.getAbortConditions().isEmpty());
    config.abortConditions.add((result, exception) -> true);
    assertEquals(1, config.getAbortConditions().size());

    EventListener<ExecutionCompletedEvent<Object>> abortListener = event -> {
    };
    config.abortListener = abortListener;
    assertSame(abortListener, config.getAbortListener());
  }
}
