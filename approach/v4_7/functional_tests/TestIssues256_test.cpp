// SITP_TEST_COUNT: 2

#include "cpp_test_harness.h"
#include "TestIssues256.h"

/** 验证未指定事件类型时生成默认的五种事件。 */
void testDefaultEventTypes() {
    TestIssues256 testCase;
    testCase.test$$onBehavior$$onWatch$without_special_EventType();
}

/** 验证同一测试对象重复构建监听不会破坏状态。 */
void testDefaultEventTypesRepeatedly() {
    TestIssues256 testCase;
    testCase.test$$onBehavior$$onWatch$without_special_EventType();
    testCase.test$$onBehavior$$onWatch$without_special_EventType();
}

/** 组装并执行 TestIssues256 功能测试。 */
int main() {
    return sitp_test::runAll({
        {"default_event_types", testDefaultEventTypes},
        {"default_event_types_repeated", testDefaultEventTypesRepeatedly},
    });
}
