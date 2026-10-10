package dev.failsafe;

import org.junit.Test;

import java.time.Duration;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertSame;
import static org.junit.Assert.assertThrows;
import static org.junit.Assert.assertTrue;

/**
 * Smoke tests for the {@link BulkheadBuilder} fragment (dev.failsafe.BulkheadBuilder).
 * The builder constructor is package-private, so this test lives in the same package.
 */
public class BulkheadBuilderSmokeTest {
  @Test
  public void build_acquireAndReleasePermits() {
    Bulkhead<Object> bulkhead = new BulkheadBuilder<>(2).build();

    assertTrue(bulkhead.tryAcquirePermit());
    assertTrue(bulkhead.tryAcquirePermit());
    assertFalse(bulkhead.tryAcquirePermit());

    bulkhead.releasePermit();
    assertTrue(bulkhead.tryAcquirePermit());
  }

  @Test
  public void build_configDefaults() {
    BulkheadConfig<Object> config = new BulkheadBuilder<>(2).build().getConfig();

    assertEquals(2, config.getMaxConcurrency());
    assertEquals(Duration.ZERO, config.getMaxWaitTime());
  }

  @Test
  public void withMaxWaitTime_setsConfig() {
    BulkheadBuilder<Object> builder = new BulkheadBuilder<>(2);

    assertSame(builder, builder.withMaxWaitTime(Duration.ofSeconds(5)));

    Bulkhead<Object> bulkhead = builder.build();
    assertEquals(Duration.ofSeconds(5), bulkhead.getConfig().getMaxWaitTime());
  }

  @Test
  public void withMaxWaitTime_null_throws() {
    BulkheadBuilder<Object> builder = new BulkheadBuilder<>(2);
    assertThrows(NullPointerException.class, () -> builder.withMaxWaitTime(null));
  }
}
