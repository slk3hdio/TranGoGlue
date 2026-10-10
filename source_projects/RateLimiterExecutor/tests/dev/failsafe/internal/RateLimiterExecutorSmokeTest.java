package dev.failsafe.internal;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

import dev.failsafe.RateLimiter;
import java.time.Duration;
import org.junit.Test;

/**
 * Smoke tests for the public API of {@link RateLimiterExecutor}.
 */
public class RateLimiterExecutorSmokeTest {

  @SuppressWarnings("unchecked")
  private RateLimiterImpl<Object> smoothLimiter(Duration maxRate) {
    return (RateLimiterImpl<Object>) RateLimiter.<Object>smoothBuilder(maxRate).build();
  }

  @Test
  public void testConstructor() {
    RateLimiterImpl<Object> limiter = smoothLimiter(Duration.ofMillis(100));
    assertEquals(0, new RateLimiterExecutor<>(limiter, 0).getPolicyIndex());
    assertEquals(3, new RateLimiterExecutor<>(limiter, 3).getPolicyIndex());
  }

  @Test
  public void testConfig() {
    RateLimiterImpl<Object> limiter = smoothLimiter(Duration.ofMillis(100));
    assertEquals(Duration.ofMillis(100), limiter.getConfig().getMaxRate());
    assertEquals(Duration.ZERO, limiter.getConfig().getMaxWaitTime());
    assertTrue(limiter.isSmooth());
    assertFalse(limiter.isBursty());
  }

  @Test
  public void testSmoothRateLimiting() {
    RateLimiterImpl<Object> limiter = smoothLimiter(Duration.ofMillis(100));
    new RateLimiterExecutor<>(limiter, 0);
    // The first permit is available immediately
    assertTrue(limiter.tryAcquirePermits(1));
    // A second permit within the same interval is not immediately available
    assertFalse(limiter.tryAcquirePermits(1));
  }

  @Test
  public void testBurstyRateLimiting() {
    RateLimiterImpl<Object> limiter = (RateLimiterImpl<Object>) RateLimiter.<Object>burstyBuilder(2,
      Duration.ofSeconds(1)).build();
    new RateLimiterExecutor<>(limiter, 0);
    assertTrue(limiter.isBursty());
    assertFalse(limiter.isSmooth());
    assertTrue(limiter.tryAcquirePermits(2));
    assertFalse(limiter.tryAcquirePermits(1));
  }
}
