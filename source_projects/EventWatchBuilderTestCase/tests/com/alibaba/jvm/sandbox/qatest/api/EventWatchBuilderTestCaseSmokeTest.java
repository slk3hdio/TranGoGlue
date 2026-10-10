package com.alibaba.jvm.sandbox.qatest.api;

import org.junit.Test;

/**
 * Smoke test for {@link EventWatchBuilderTestCase}.
 *
 * <p>The fragment's same-named class is itself an upstream JUnit 4 test class. Each of its public
 * {@code test$$} methods drives {@link com.alibaba.jvm.sandbox.api.listener.ext.EventWatchBuilder}
 * with the in-fragment {@code MockForBuilderModuleEventWatcher} mock (no real jvm-sandbox runtime
 * needed) and asserts on the recorded event types / watch condition filters. We instantiate the
 * class and invoke each upstream test method directly.
 */
public class EventWatchBuilderTestCaseSmokeTest {

    @Test
    public void testNormal() {
        new EventWatchBuilderTestCase().test$$EventWatchBuilder$$normal$$normal();
    }

    @Test
    public void testAll() {
        new EventWatchBuilderTestCase().test$$EventWatchBuilder$$normal$$all();
    }

    @Test
    public void testCallOnly() {
        new EventWatchBuilderTestCase().test$$EventWatchBuilder$$normal$$CallOnly();
    }

    @Test
    public void testLineOnly() {
        new EventWatchBuilderTestCase().test$$EventWatchBuilder$$normal$$LineOnly();
    }

    @Test
    public void testRegex() {
        new EventWatchBuilderTestCase().test$$EventWatchBuilder$$regex();
    }
}
