package net.sf.cglib.transform.impl;

import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertTrue;

import java.io.IOException;
import java.lang.reflect.UndeclaredThrowableException;

import net.sf.cglib.core.ClassGenerator;
import net.sf.cglib.core.DefaultGeneratorStrategy;
import net.sf.cglib.core.GeneratorStrategy;

import org.junit.Test;
import org.objectweb.asm.ClassVisitor;
import org.objectweb.asm.Opcodes;

/**
 * Smoke tests for the {@link UndeclaredThrowableStrategy} fragment class
 * (net.sf.cglib.transform.impl.UndeclaredThrowableStrategy).
 *
 * <p>Note: the source declares no public {@code accept(...)} method on this
 * class (the {@code accept} filter lives on a private static anonymous
 * {@code MethodFilter}), so the tests exercise the public surface:
 * constructor, type contract, {@code toString}, and the public
 * {@code generate(ClassGenerator)} path inherited from
 * {@link DefaultGeneratorStrategy}.</p>
 */
public class UndeclaredThrowableStrategySmokeTest {

    @Test
    public void testConstructorSmoke() {
        UndeclaredThrowableStrategy s1 = new UndeclaredThrowableStrategy(IOException.class);
        assertNotNull(s1);
        UndeclaredThrowableStrategy s2 = new UndeclaredThrowableStrategy(UndeclaredThrowableException.class);
        assertNotNull(s2);
        assertTrue(s1 instanceof GeneratorStrategy);
        assertTrue(s1 instanceof DefaultGeneratorStrategy);
    }

    @Test
    public void testToStringContainsClassName() {
        UndeclaredThrowableStrategy s = new UndeclaredThrowableStrategy(IOException.class);
        assertTrue(s.toString().contains("UndeclaredThrowableStrategy"));
    }

    @Test
    public void testGenerateEmptyClass() throws Exception {
        UndeclaredThrowableStrategy strategy = new UndeclaredThrowableStrategy(IOException.class);
        ClassGenerator cg = new ClassGenerator() {
            public void generateClass(ClassVisitor v) throws Exception {
                v.visit(Opcodes.V1_8, Opcodes.ACC_PUBLIC, "net/sf/cglib/test/Empty", null, "java/lang/Object", null);
                v.visitEnd();
            }
        };
        byte[] bytes = strategy.generate(cg);
        assertNotNull(bytes);
        assertTrue(bytes.length > 0);
    }
}
