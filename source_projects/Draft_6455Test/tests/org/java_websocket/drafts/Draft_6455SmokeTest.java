package org.java_websocket.drafts;

import org.junit.Test;

/**
 * JUnit 4 smoke test for the fragment class {@link Draft_6455Test}.
 *
 * <p>The fragment itself is an upstream JUnit 5 test class: its public test methods are plain
 * methods (they internally use junit-jupiter Assertions) and are fully self-contained — each one
 * builds its own {@link Draft_6455} instances and only relies on the handshake data initialized
 * in the public constructor. We therefore instantiate it and invoke a subset of those methods
 * directly.
 */
public class Draft_6455SmokeTest {

    private final Draft_6455Test upstream = new Draft_6455Test();

    @Test
    public void constructorRejectsInvalidArguments() throws Exception {
        upstream.testConstructor();
    }

    @Test
    public void defaultExtensionIsReturned() throws Exception {
        upstream.testGetExtension();
    }

    @Test
    public void knownExtensionsReflectProvidedExtensions() throws Exception {
        upstream.testGetKnownExtensions();
    }

    @Test
    public void protocolNegotiationThroughHandshake() throws Exception {
        upstream.testGetProtocol();
    }

    @Test
    public void copyInstanceProducesIndependentDraft() throws Exception {
        upstream.testCopyInstance();
    }

    @Test
    public void resetRestoresDefaultState() throws Exception {
        upstream.testReset();
    }
}
