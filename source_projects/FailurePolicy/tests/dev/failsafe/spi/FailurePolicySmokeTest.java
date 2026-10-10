package dev.failsafe.spi;

import dev.failsafe.FailurePolicyConfig;
import dev.failsafe.FailurePolicyTestSupport;
import org.junit.Test;

import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * Smoke tests for the {@link FailurePolicy} fragment (dev.failsafe.spi.FailurePolicy).
 * {@code isFailure} is exercised through an anonymous implementation backed by a real {@link FailurePolicyConfig}.
 */
public class FailurePolicySmokeTest {
  private FailurePolicy<Object> policyWith(FailurePolicyConfig<Object> config) {
    return new FailurePolicy<Object>() {
      @Override
      public FailurePolicyConfig<Object> getConfig() {
        return config;
      }

      @Override
      public PolicyExecutor<Object> toExecutor(int policyIndex) {
        return null;
      }
    };
  }

  @Test
  public void noConditions_exceptionIsFailure() {
    FailurePolicy<Object> policy = policyWith(FailurePolicyTestSupport.newConfig());

    assertTrue(policy.isFailure("result", new IllegalStateException("boom")));
    assertFalse(policy.isFailure("result", null));
  }

  @Test
  public void handleResult_matchingResultIsFailure() {
    FailurePolicy<Object> policy = policyWith(FailurePolicyTestSupport.configWithResultHandling("x"));

    assertTrue(policy.isFailure("x", null));
    assertFalse(policy.isFailure("y", null));
  }

  @Test
  public void unmatchedResult_withUncheckedException_isFailure() {
    FailurePolicy<Object> policy = policyWith(FailurePolicyTestSupport.configWithResultHandling("x"));

    // Result does not match any condition and exceptions were not "checked" by a condition, so the exception is a failure
    assertTrue(policy.isFailure("y", new IllegalStateException("boom")));
  }

  @Test
  public void handledException_matchingIsFailure_nonMatchingIsNot() {
    FailurePolicy<Object> policy =
      policyWith(FailurePolicyTestSupport.configWithExceptionHandling(IllegalArgumentException.class));

    assertTrue(policy.isFailure(null, new IllegalArgumentException("bad")));
    // Exceptions are checked by a condition, so a non-matching exception is not a failure
    assertFalse(policy.isFailure(null, new IllegalStateException("bad")));
  }
}
