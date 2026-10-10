package com.alibaba.jvm.sandbox.qatest.api;

import org.junit.Assert;
import org.junit.Test;

import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/**
 * Smoke test for {@link AdviceListenerTestCase}.
 *
 * <p>The fragment's same-named class is itself an upstream JUnit 4 test class. It is fully
 * self-contained: it drives {@link com.alibaba.jvm.sandbox.api.listener.ext.EventWatchBuilder}
 * with the in-fragment {@code MockForBuilderModuleEventWatcher} mock and needs no real
 * jvm-sandbox runtime. So the smoke test simply instantiates the class and invokes its public
 * {@code test$$} method directly.
 */
public class AdviceListenerTestCaseSmokeTest {

    private static final String TEST_METHOD_NAME = "test$$AdviceListener$$onBefore$onReturn$onThrows";

    /**
     * The upstream test method must be public, void and present on the class under test.
     */
    @Test
    public void testUpstreamTestMethodIsPublicVoid() throws Exception {
        final Method method = AdviceListenerTestCase.class.getMethod(TEST_METHOD_NAME);
        Assert.assertNotNull(method);
        Assert.assertTrue(Modifier.isPublic(method.getModifiers()));
        Assert.assertEquals(void.class, method.getReturnType());
    }

    /**
     * Directly run the upstream test body: registers an AdviceListener through the builder and
     * replays Before/Return and Before/Throws event pairs through the mock watcher's listener,
     * asserting the recorded trace ("before;afterReturning;" / "before;afterThrowing;").
     */
    @Test
    public void testOnBeforeOnReturnOnThrows() throws Throwable {
        new AdviceListenerTestCase().test$$AdviceListener$$onBefore$onReturn$onThrows();
    }
}
