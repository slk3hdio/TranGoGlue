package com.alibaba.jvm.sandbox.qatest.api.issues;

import org.junit.Test;

/**
 * TestIssues256 冒烟测试。
 * TestIssues256 本身是上游测试类, 其公有方法
 * test$$onBehavior$$onWatch$without_special_EventType() 自包含
 * (基于 MockForBuilderModuleEventWatcher + EventWatchBuilder, 不依赖容器插桩),
 * 因此直接实例化并调用。
 */
public class TestIssues256SmokeTest {

    @Test
    public void invokeUpstreamTestMethod() {
        new TestIssues256().test$$onBehavior$$onWatch$without_special_EventType();
    }

    @Test
    public void invokeUpstreamTestMethodRepeatedly() {
        final TestIssues256 test = new TestIssues256();
        test.test$$onBehavior$$onWatch$without_special_EventType();
        test.test$$onBehavior$$onWatch$without_special_EventType();
    }

}
