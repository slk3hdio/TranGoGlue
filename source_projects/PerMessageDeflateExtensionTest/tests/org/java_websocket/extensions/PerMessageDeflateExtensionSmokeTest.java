package org.java_websocket.extensions;

import org.junit.Test;

/**
 * JUnit 4 smoke test for the fragment class {@link PerMessageDeflateExtensionTest}.
 *
 * <p>The fragment itself is an upstream JUnit 5 test class: its public test methods are plain
 * methods (they internally use junit-jupiter Assertions) and are fully self-contained. We
 * therefore instantiate it and invoke a subset of those methods directly.
 */
public class PerMessageDeflateExtensionSmokeTest {

    private final PerMessageDeflateExtensionTest upstream = new PerMessageDeflateExtensionTest();

    @Test
    public void defaultsMatchSpec() {
        upstream.testDefaults();
    }

    @Test
    public void toStringReturnsExtensionName() {
        upstream.testToString();
    }

    @Test
    public void copyInstancePreservesConfiguration() {
        upstream.testCopyInstance();
    }

    @Test
    public void frameValidationEnforcesRsvRules() {
        upstream.testIsFrameValid();
    }

    @Test
    public void serverAcceptsProvidedExtension() {
        upstream.testAcceptProvidedExtensionAsServer();
    }

    @Test
    public void decodeRoundTripsDeflatedPayload() throws Exception {
        upstream.testDecodeFrame();
    }
}
