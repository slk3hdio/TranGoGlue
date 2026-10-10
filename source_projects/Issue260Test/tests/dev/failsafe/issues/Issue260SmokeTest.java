package dev.failsafe.issues;

import org.junit.Test;

/**
 * Smoke test for the {@link Issue260Test} fragment (dev.failsafe.issues.Issue260Test).
 * The upstream TestNG test is self-contained (uses its own single-thread executor, ~1s) and is invoked directly from a
 * JUnit 4 test. It does not depend on any external resources.
 */
public class Issue260SmokeTest {
  @Test
  public void test() throws Throwable {
    new Issue260Test().test();
  }
}
