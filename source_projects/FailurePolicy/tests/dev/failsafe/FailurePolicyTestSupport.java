package dev.failsafe;

import java.util.Collections;

/**
 * Test support for exercising {@link FailurePolicyConfig} from outside the {@code dev.failsafe.spi} test package.
 * {@link FailurePolicyConfig} has a protected constructor and package-private condition fields; conditions are wired
 * using the real package-private predicate factories on {@link FailurePolicyBuilder}.
 */
public final class FailurePolicyTestSupport {
  private FailurePolicyTestSupport() {
  }

  /** Returns a fresh, unconfigured {@link FailurePolicyConfig}. */
  public static <R> FailurePolicyConfig<R> newConfig() {
    return new FailurePolicyConfig<R>() {
    };
  }

  /** Returns a config that treats {@code result} as a failure (equivalent to {@code handleResult(result)}). */
  public static <R> FailurePolicyConfig<R> configWithResultHandling(R result) {
    FailurePolicyConfig<R> config = newConfig();
    config.failureConditions.add(FailurePolicyBuilder.resultPredicateFor(result));
    return config;
  }

  /** Returns a config that treats exceptions assignable from {@code failure} as failures (equivalent to {@code handle}). */
  public static <R> FailurePolicyConfig<R> configWithExceptionHandling(Class<? extends Throwable> failure) {
    FailurePolicyConfig<R> config = newConfig();
    config.exceptionsChecked = true;
    config.failureConditions.add(FailurePolicyBuilder.failurePredicateFor(Collections.singletonList(failure)));
    return config;
  }
}
