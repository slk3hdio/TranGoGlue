package dev.failsafe;

import org.junit.Test;

import java.time.Duration;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

/**
 * Smoke tests for the {@link RateLimiterBuilder} fragment (dev.failsafe.RateLimiterBuilder).
 * The builder constructors are package-private, so this test lives in the same package.
 */
public class RateLimiterBuilderSmokeTest {
  @Test
  public void build_bursty_limitsPermitsPerPeriod() {
    // Bursty: 2 permits per 1 hour period -> at most 2 immediate acquisitions
    RateLimiter<Object> rateLimiter = new RateLimiterBuilder<>(2, Duration.ofHours(1)).build();

    assertTrue(rateLimiter.isBursty());
    assertFalse(rateLimiter.isSmooth());

    assertTrue(rateLimiter.tryAcquirePermit());
    assertTrue(rateLimiter.tryAcquirePermit());
    assertFalse(rateLimiter.tryAcquirePermit());
  }

  @Test
  public void build_smooth_limitsRate() {
    // Smooth: at most one permit per 60 seconds -> a second immediate acquisition must fail
    RateLimiter<Object> rateLimiter = new RateLimiterBuilder<>(Duration.ofSeconds(60)).build();

    assertTrue(rateLimiter.isSmooth());
    assertFalse(rateLimiter.isBursty());

    assertTrue(rateLimiter.tryAcquirePermit());
    assertFalse(rateLimiter.tryAcquirePermit());
  }

  @Test
  public void withMaxWaitTime_setsConfig() {
    RateLimiterBuilder<Object> builder = new RateLimiterBuilder<>(Duration.ofSeconds(1));

    // Default max wait time is Duration.ZERO
    assertEquals(Duration.ZERO, builder.build().getConfig().getMaxWaitTime());

    assertSame(builder, builder.withMaxWaitTime(Duration.ofSeconds(5)));
    assertEquals(Duration.ofSeconds(5), builder.build().getConfig().getMaxWaitTime());
  }

  @Test
  public void withMaxWaitTime_null_throws() {
    RateLimiterBuilder<Object> builder = new RateLimiterBuilder<>(Duration.ofSeconds(1));
    assertThrows(NullPointerException.class, () -> builder.withMaxWaitTime(null));
  }
}
