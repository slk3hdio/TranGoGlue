package dev.failsafe.issues;

import org.junit.Test;

/**
 * Smoke test for the {@link Issue231Test} fragment (dev.failsafe.issues.Issue231Test).
 * The upstream TestNG test is self-contained (real Failsafe timeout + interrupt behavior, ~1.3s) and is invoked
 * directly from a JUnit 4 test.
 */
public class Issue231SmokeTest {
  @Test
  public void shouldWaitForExecutionCompletion() {
    new Issue231Test().shouldWaitForExecutionCompletion();
  }
}
