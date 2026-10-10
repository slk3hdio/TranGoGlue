package com.alibaba.jvm.sandbox.qatest.core.util.matcher;

import com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructure;
import com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructureFactory;
import com.alibaba.jvm.sandbox.qatest.core.util.matcher.target.ChildClass;
import org.junit.Assert;
import org.junit.Test;

import java.lang.reflect.Constructor;
import java.lang.reflect.Method;
import java.lang.reflect.Modifier;

/**
 * Smoke test for {@link ClassStructureByChildClassTestCase}.
 *
 * <p>The fragment's same-named class is an upstream JUnit 4 parameterized test. Its static
 * {@code getData()} yields two {@link ClassStructure} rows for {@code ChildClass}:
 * <ol>
 *   <li>{@code ClassStructureFactory.createClassStructure(ChildClass.class)} — JDK reflection impl;</li>
 *   <li>{@code ClassStructureFactory.createClassStructure(toByteArray(ChildClass.class), ...)} —
 *       ASM impl parsed from the class-file byte array.</li>
 * </ol>
 *
 * <p>Environment note: the ASM row cannot run here. {@code build.bat} compiles the fragment with
 * the local JDK (Java 25, class-file major version 69) while {@code deps\lib} pins ASM 9.4, which
 * supports at most Java 20 (major 64); constructing the ASM structure throws
 * {@code IllegalArgumentException: Unsupported class file major version 69}. Since the classpath
 * order puts {@code deps\lib} first and both build scripts are immutable, the row is skipped.
 * Per the runnable-subset fallback, this smoke test drives the class exactly like
 * {@code getData()}'s first row: {@code ClassStructureFactory.createClassStructure(ChildClass.class)}
 * (pure JDK reflection, no ASM), then instantiates the test case and invokes representative public
 * {@code test$$} methods directly.
 */
public class ClassStructureByChildClassTestCaseSmokeTest {

    /**
     * Upstream API surface: a public constructor taking a single ClassStructure, and public void
     * test$$ methods (the test-case body that would have been parameterized by getData()).
     */
    @Test
    public void testUpstreamTestMethodSurface() throws Exception {
        final Constructor<ClassStructureByChildClassTestCase> ctor =
                ClassStructureByChildClassTestCase.class.getConstructor(ClassStructure.class);
        Assert.assertNotNull(ctor);
        Assert.assertTrue(Modifier.isPublic(ctor.getModifiers()));

        int testMethodCount = 0;
        for (final Method method : ClassStructureByChildClassTestCase.class.getDeclaredMethods()) {
            if (method.getName().startsWith("test$$")) {
                Assert.assertTrue("test$$ method must be public: " + method.getName(),
                        Modifier.isPublic(method.getModifiers()));
                Assert.assertEquals(void.class, method.getReturnType());
                testMethodCount++;
            }
        }
        Assert.assertTrue("expected at least one test$$ method", testMethodCount > 0);
    }

    /**
     * Main structure assertions (class name, access, supers, interfaces, family types,
     * annotations and behavior sign codes) against the JDK reflection structure.
     */
    @Test
    public void testChildClassStructureFromJdkImpl() throws Throwable {
        final ClassStructureByChildClassTestCase testCase = newTestCaseFromJdkStructure();
        testCase.test$$ChildClassStructure();
    }

    /**
     * Method return-type structure assertions against the JDK reflection structure.
     */
    @Test
    public void testMethodOfReturnFromJdkImpl() throws Throwable {
        final ClassStructureByChildClassTestCase testCase = newTestCaseFromJdkStructure();
        testCase.test$$ChildClassStructure$$methodOfReturn();
    }

    /**
     * Method annotation/exception assertions against the JDK reflection structure.
     */
    @Test
    public void testMethodOfChildClassWithAnnotationFromJdkImpl() throws Throwable {
        final ClassStructureByChildClassTestCase testCase = newTestCaseFromJdkStructure();
        testCase.test$$ChildClassStructure$$methodOfChildClassWithAnnotation();
    }

    private static ClassStructureByChildClassTestCase newTestCaseFromJdkStructure() {
        final ClassStructure structure = ClassStructureFactory.createClassStructure(ChildClass.class);
        Assert.assertNotNull(structure);
        return new ClassStructureByChildClassTestCase(structure);
    }
}
