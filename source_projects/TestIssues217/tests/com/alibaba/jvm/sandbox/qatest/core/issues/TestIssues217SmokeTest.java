package com.alibaba.jvm.sandbox.qatest.core.issues;

import com.alibaba.jvm.sandbox.api.event.Event;
import com.alibaba.jvm.sandbox.api.listener.EventListener;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchBuilder;
import com.alibaba.jvm.sandbox.api.listener.ext.EventWatchCondition;
import com.alibaba.jvm.sandbox.core.util.matcher.Matcher;
import com.alibaba.jvm.sandbox.qatest.core.enhance.target.Calculator;
import com.alibaba.jvm.sandbox.qatest.core.enhance.target.MyCalculator;
import org.junit.Test;

import static com.alibaba.jvm.sandbox.core.util.matcher.structure.ClassStructureFactory.createClassStructure;
import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertFalse;
import static org.junit.Assert.assertNotNull;
import static org.junit.Assert.assertNull;
import static org.junit.Assert.assertTrue;

/**
 * TestIssues217 冒烟测试。
 * TestIssues217 本身是上游测试类, 公有测试方法大多自包含, 可直接实例化调用。
 *
 * 注意: matchingComputerAnnotation() / matchingInheritedComputerAnnotation()
 * 内部通过 createClassStructure(byte[], ClassLoader) 走 ASM(asm-9.4) 解析
 * 本地 javac 编译出的类文件; 本机 JDK 为 25(类文件 major 69), 超出 asm-9.4
 * 支持的版本上限, 抛 "Unsupported class file major version 69"。这是工具链版本
 * 不匹配的本地环境限制(上游 CI 使用老 JDK), 因此这两个上游方法在此跳过,
 * 改用仅走 JDK 反射路径(createClassStructure(Class))的方式复现同样的匹配语义。
 */
public class TestIssues217SmokeTest {

    // 上游方法 matchingComputerAnnotation() 与 matchingInheritedComputerAnnotation()
    // 因 asm-9.4 无法解析 JDK 25 类文件(major 69)而跳过, 原因见类注释。

    @Test
    public void invokeMatchingTestAOrTestBAnnotation() {
        // 自包含: 仅使用 JDK 反射类结构, 本机可直接运行
        new TestIssues217().matching__TestA_or_TestB__Annotation();
    }

    @Test
    public void matchingComputerAnnotation_viaJdkClassStructure() {
        final TestIssues217 outer = new TestIssues217();
        final TestIssues217.GetMatcherModuleEventWatcher watcher
                = outer.new GetMatcherModuleEventWatcher();

        new EventWatchBuilder(watcher)
                .onClass("*")
                .hasAnnotationTypes("com.alibaba.jvm.sandbox.qatest.core.enhance.target.Computer")
                .onAnyBehavior()
                .onWatch(noopEventListener());

        final Matcher matcher = watcher.getMatcher();
        // Calculator 声明了 @Computer → 匹配
        assertTrue(matcher.matching(createClassStructure(Calculator.class)).isMatched());
        // MyCalculator 仅继承(非 @Inherited 的)@Computer → 不匹配
        assertFalse(matcher.matching(createClassStructure(MyCalculator.class)).isMatched());
        // TestIssues217 无 @Computer → 不匹配
        assertFalse(matcher.matching(createClassStructure(TestIssues217.class)).isMatched());
    }

    @Test
    public void matchingInheritedComputerAnnotation_viaJdkClassStructure() {
        final TestIssues217 outer = new TestIssues217();
        final TestIssues217.GetMatcherModuleEventWatcher watcher
                = outer.new GetMatcherModuleEventWatcher();

        new EventWatchBuilder(watcher)
                .onClass("*")
                .hasAnnotationTypes("com.alibaba.jvm.sandbox.qatest.core.enhance.target.InheritedComputer")
                .onAnyBehavior()
                .onWatch(noopEventListener());

        final Matcher matcher = watcher.getMatcher();
        // Calculator 声明了 @InheritedComputer → 匹配
        assertTrue(matcher.matching(createClassStructure(Calculator.class)).isMatched());
        // MyCalculator 经父类 Calculator 继承 @InheritedComputer → 匹配
        assertTrue(matcher.matching(createClassStructure(MyCalculator.class)).isMatched());
        // TestIssues217 无该注解 → 不匹配
        assertFalse(matcher.matching(createClassStructure(TestIssues217.class)).isMatched());
    }

    @Test
    public void getConditionAndMatcher_basicBehavior() {
        final TestIssues217 outer = new TestIssues217();
        final TestIssues217.GetMatcherModuleEventWatcher watcher
                = outer.new GetMatcherModuleEventWatcher();

        // 尚未发起 watch 之前, 条件为空
        assertNull(watcher.getCondition());

        new EventWatchBuilder(watcher)
                .onClass("com.alibaba.jvm.sandbox.qatest.core.enhance.target.Calculator")
                .onBehavior("add")
                .onWatch(noopEventListener());

        // watch 之后, 条件与匹配器可用
        final EventWatchCondition condition = watcher.getCondition();
        assertNotNull(condition);
        assertEquals(1, condition.getOrFilterArray().length);
        final Matcher matcher = watcher.getMatcher();
        assertNotNull(matcher);
        // Calculator 的 add 行为应匹配; MyCalculator 类名不匹配 → 不匹配
        assertTrue(matcher.matching(createClassStructure(Calculator.class)).isMatched());
        assertFalse(matcher.matching(createClassStructure(MyCalculator.class)).isMatched());
    }

    private static EventListener noopEventListener() {
        return new EventListener() {
            @Override
            public void onEvent(Event event) throws Throwable {
            }
        };
    }

}
