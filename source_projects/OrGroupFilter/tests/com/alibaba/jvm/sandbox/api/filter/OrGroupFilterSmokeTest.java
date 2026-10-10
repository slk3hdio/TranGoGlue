package com.alibaba.jvm.sandbox.api.filter;

import org.junit.Test;

import java.util.concurrent.atomic.AtomicInteger;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertTrue;

/**
 * OrGroupFilter 冒烟测试: 用匿名 Filter 组合验证 OR 语义。
 * doClassFilter: 任一子过滤器返回 true 则结果为 true;
 * doMethodFilter: 复用最近一次 doClassFilter 成功时的类信息(_doClassFilter), 再判断方法是否匹配。
 */
public class OrGroupFilterSmokeTest {

    /**
     * 构造一个固定返回值的过滤器, 并可记录被调用的次数。
     */
    private static Filter constFilter(final boolean result, final AtomicInteger classCallCount) {
        return new Filter() {
            @Override
            public boolean doClassFilter(int access,
                                         String javaClassName,
                                         String superClassTypeJavaClassName,
                                         String[] interfaceTypeJavaClassNameArray,
                                         String[] annotationTypeJavaClassNameArray) {
                classCallCount.incrementAndGet();
                return result;
            }

            @Override
            public boolean doMethodFilter(int access,
                                          String javaMethodName,
                                          String[] parameterTypeJavaClassNameArray,
                                          String[] throwsTypeJavaClassNameArray,
                                          String[] annotationTypeJavaClassNameArray) {
                return result;
            }
        };
    }

    @Test
    public void doClassFilter_trueWhenAnyFilterMatches() {
        final OrGroupFilter group = new OrGroupFilter(
                constFilter(false, new AtomicInteger()),
                constFilter(true, new AtomicInteger())
        );
        assertTrue(group.doClassFilter(1, "A", null, null, null));
    }

    @Test
    public void doClassFilter_falseWhenAllFiltersReject() {
        final OrGroupFilter group = new OrGroupFilter(
                constFilter(false, new AtomicInteger()),
                constFilter(false, new AtomicInteger())
        );
        assertFalse(group.doClassFilter(1, "A", null, null, null));
    }

    @Test
    public void doClassFilter_shortCircuitsOnFirstTrue() {
        final AtomicInteger firstCalls = new AtomicInteger();
        final AtomicInteger secondCalls = new AtomicInteger();
        final OrGroupFilter group = new OrGroupFilter(
                constFilter(true, firstCalls),
                constFilter(true, secondCalls)
        );
        assertTrue(group.doClassFilter(1, "A", null, null, null));
        assertEquals(1, firstCalls.get());
        assertEquals(0, secondCalls.get());
    }

    @Test
    public void doMethodFilter_matchesWhenClassAndMethodBothMatch() {
        // f1: 类不匹配但方法永远匹配; f2: 仅 "Target"/"run" 匹配
        final Filter f1 = new Filter() {
            @Override
            public boolean doClassFilter(int access, String javaClassName, String superClassTypeJavaClassName,
                                         String[] interfaceTypeJavaClassNameArray, String[] annotationTypeJavaClassNameArray) {
                return false;
            }

            @Override
            public boolean doMethodFilter(int access, String javaMethodName,
                                          String[] parameterTypeJavaClassNameArray, String[] throwsTypeJavaClassNameArray,
                                          String[] annotationTypeJavaClassNameArray) {
                return true;
            }
        };
        final Filter f2 = new Filter() {
            @Override
            public boolean doClassFilter(int access, String javaClassName, String superClassTypeJavaClassName,
                                         String[] interfaceTypeJavaClassNameArray, String[] annotationTypeJavaClassNameArray) {
                return "Target".equals(javaClassName);
            }

            @Override
            public boolean doMethodFilter(int access, String javaMethodName,
                                          String[] parameterTypeJavaClassNameArray, String[] throwsTypeJavaClassNameArray,
                                          String[] annotationTypeJavaClassNameArray) {
                return "run".equals(javaMethodName);
            }
        };

        final OrGroupFilter group = new OrGroupFilter(f1, f2);

        // doClassFilter 成功后, doMethodFilter 复用存储的类信息进行 OR 判断
        assertTrue(group.doClassFilter(1, "Target", null, null, null));
        assertTrue(group.doMethodFilter(1, "run", null, null, null));
        assertFalse(group.doMethodFilter(1, "other", null, null, null));
    }

    @Test
    public void nullConstructorArg_handledAsEmptyGroup() {
        final OrGroupFilter group = new OrGroupFilter((Filter[]) null);
        assertFalse(group.doClassFilter(1, "A", null, null, null));
        assertFalse(group.doMethodFilter(1, "m", null, null, null));
    }

}
