package dev.failsafe;

import dev.failsafe.function.ContextualSupplier;

import java.time.Duration;

/**
 * Test support for exercising {@link DelayablePolicyConfig} from outside the {@code dev.failsafe.spi} test package.
 * {@link DelayablePolicyConfig} has a protected constructor and package-private {@code delayFn} field, so the config is
 * built through a concrete {@link DelayablePolicyBuilder} subclass (the real public configuration API) which lives in
 * the same package as the config.
 */
public final class DelayablePolicyTestSupport {
  private DelayablePolicyTestSupport() {
  }

  static final class ConcreteDelayablePolicyBuilder<R> extends
    DelayablePolicyBuilder<ConcreteDelayablePolicyBuilder<R>, DelayablePolicyConfig<R>, R> {
    ConcreteDelayablePolicyBuilder(DelayablePolicyConfig<R> config) {
      super(config);
    }
  }

  /** Returns a fresh, unconfigured {@link DelayablePolicyConfig}. */
  public static <R> DelayablePolicyConfig<R> newConfig() {
    return new DelayablePolicyConfig<R>() {
    };
  }

  /** Returns a {@link DelayablePolicyConfig} whose delay function is {@code delayFn}. */
  public static <R> DelayablePolicyConfig<R> configWithDelayFn(ContextualSupplier<R, Duration> delayFn) {
    DelayablePolicyConfig<R> config = newConfig();
    new ConcreteDelayablePolicyBuilder<>(config).withDelayFn(delayFn);
    return config;
  }
}
